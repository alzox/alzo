"""
Acoustic echo cancellation for an open mic.

A background thread records what the computer is playing (WASAPI loopback of the
default output device) into a ring buffer. For every mic clip we grab the matching
slice of that playback, align it to the mic, and subtract it with a partitioned-block
frequency-domain NLMS adaptive filter, followed by a light residual-echo suppressor.

If nothing is playing (or loopback is unavailable) the mic audio passes through untouched.
"""
import threading
import time

import numpy as np
import speech_recognition as sr
from scipy.signal import resample_poly, stft, istft

try:
    import pyaudiowpatch as pyaudio
except ImportError:  # loopback capture needs the WASAPI fork of PyAudio
    pyaudio = None

RATE = 16000           # processing / output rate (what whisper wants anyway)
BUFFER_SECONDS = 15    # how much playback history to keep
PRE_ROLL = 0.6         # seconds of playback before the mic clip to search for the echo delay
SILENCE_RMS = 1e-3     # playback quieter than this is treated as silence -> skip AEC

# adaptive filter settings
BLOCK = 256            # samples per block (16 ms)
PARTITIONS = 12        # filter length = BLOCK * PARTITIONS (~190 ms of room echo)
MU = 0.3               # NLMS step size
DT_LOW, DT_HIGH = 0.5, 0.8  # playback/mic coherence: below LOW = user talking (freeze), above HIGH = echo only
GUARD = 64             # samples of slack before the detected delay (filter stays causal)


class LoopbackRecorder:
    def __init__(self):
        self._lock = threading.Lock()
        self._buf = None
        self._rate = None
        self._written = 0        # total samples ever written
        self._t_last = 0.0       # monotonic time of the newest sample
        self._device_name = None
        self._stop = threading.Event()

    # -- capture ---------------------------------------------------------
    def start(self):
        if pyaudio is None:
            print("echo cancel disabled: `pip install pyaudiowpatch` for loopback capture")
            return False
        threading.Thread(target=self._run, daemon=True).start()
        return True

    def _callback(self, in_data, frame_count, time_info, status):
        samples = np.frombuffer(in_data, dtype=np.float32).reshape(-1, self._channels).mean(axis=1)
        now = time.monotonic()
        with self._lock:
            # WASAPI loopback delivers nothing while the output is silent;
            # fill that gap with zeros so time -> sample mapping stays right.
            expected = self._t_last + frame_count / self._rate
            gap = int((now - expected) * self._rate)
            if self._t_last and gap > self._rate // 20:
                self._write(np.zeros(min(gap, len(self._buf)), dtype=np.float32))
            self._write(samples)
            self._t_last = now
        return (None, pyaudio.paContinue)

    def _write(self, samples):
        n = len(samples)
        size = len(self._buf)
        if n >= size:
            samples, n = samples[-size:], size
        start = self._written % size
        end = start + n
        if end <= size:
            self._buf[start:end] = samples
        else:
            split = size - start
            self._buf[start:] = samples[:split]
            self._buf[:n - split] = samples[split:]
        self._written += n

    def _open(self, p):
        dev = p.get_default_wasapi_loopback()
        self._rate = int(dev["defaultSampleRate"])
        self._channels = max(1, int(dev["maxInputChannels"]))
        with self._lock:
            self._buf = np.zeros(self._rate * BUFFER_SECONDS, dtype=np.float32)
            self._written = 0
            self._t_last = 0.0
        self._device_name = dev["name"]
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=self._channels,
            rate=self._rate,
            input=True,
            input_device_index=dev["index"],
            frames_per_buffer=self._rate // 50,
            stream_callback=self._callback,
        )
        print(f"echo cancel listening to: {self._device_name}")
        return stream

    def _run(self):
        while not self._stop.is_set():
            p = pyaudio.PyAudio()
            stream = None
            try:
                stream = self._open(p)
                # reopen if the default output device changes (e.g. headphones plugged in)
                while not self._stop.is_set() and stream.is_active():
                    time.sleep(2)
                    if p.get_default_wasapi_loopback()["name"] != self._device_name:
                        break
            except Exception as e:
                print(f"loopback capture error: {e}")
                time.sleep(2)
            finally:
                try:
                    if stream is not None:
                        stream.close()
                    p.terminate()
                except Exception:
                    pass

    # -- reading ---------------------------------------------------------
    def window(self, t_end, duration):
        """Playback (mono, RATE Hz) from t_end - duration - PRE_ROLL to t_end, or None."""
        with self._lock:
            if self._buf is None or not self._t_last:
                return None
            rate, size = self._rate, len(self._buf)
            n = int((duration + PRE_ROLL) * rate)
            # index (in absolute samples) of t_end
            end_idx = self._written - int((self._t_last - t_end) * rate)
            start_idx = end_idx - n
            out = np.zeros(n, dtype=np.float32)
            lo = max(start_idx, self._written - size, 0)
            hi = min(end_idx, self._written)
            if hi > lo:
                idx = np.arange(lo, hi) % size
                out[lo - start_idx:hi - start_idx] = self._buf[idx]
        return _resample(out, rate, RATE)


def _resample(x, src, dst):
    if src == dst:
        return x.astype(np.float32)
    g = np.gcd(int(src), int(dst))
    return resample_poly(x, dst // g, src // g).astype(np.float32)


def _find_delay(mic, ref, max_lag):
    """Lag (samples) at which ref best lines up with mic, searching 0..max_lag."""
    n = len(mic) + len(ref)
    nfft = 1 << (n - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(ref, nfft) * np.conj(np.fft.rfft(mic, nfft)), nfft)
    corr = np.abs(corr[:max_lag + 1])
    return int(np.argmax(corr))


def _nlms(mic, ref, W=None):
    """Partitioned-block frequency-domain NLMS. Returns (error, echo_estimate, weights)."""
    B, P, N = BLOCK, PARTITIONS, 2 * BLOCK
    F = B + 1
    blocks = len(mic) // B
    W = np.zeros((P, F), dtype=np.complex128) if W is None else W.copy()
    X = np.zeros((P, F), dtype=np.complex128)
    x_buf = np.zeros(N)
    d_buf = np.zeros(N)
    power = None
    Sxx = np.full(F, 1e-6)
    Sdd = np.full(F, 1e-6)
    Sxd = np.zeros(F, dtype=np.complex128)
    err = np.zeros(blocks * B)
    est = np.zeros(blocks * B)
    for k in range(blocks):
        sl = slice(k * B, (k + 1) * B)
        d = mic[sl]
        x_buf = np.concatenate([x_buf[B:], ref[sl]])
        d_buf = np.concatenate([d_buf[B:], d])
        X = np.roll(X, 1, axis=0)
        X[0] = np.fft.rfft(x_buf)

        y = np.fft.irfft((X * W).sum(axis=0), N)[B:]
        e = d - y
        if np.dot(e, e) > 2 * np.dot(d, d) + 1e-9:
            W *= 0.5          # filter is making things worse: back off, pass the mic through
            e, y = d, np.zeros(B)
        err[sl], est[sl] = e, y

        # double-talk detector: how much of the mic is explained by the playback?
        # (coherence between far-end and mic doesn't need a converged filter)
        D = np.fft.rfft(d_buf)
        Sxx = 0.85 * Sxx + 0.15 * np.abs(X[0]) ** 2
        Sdd = 0.85 * Sdd + 0.15 * np.abs(D) ** 2
        Sxd = 0.85 * Sxd + 0.15 * np.conj(X[0]) * D
        xi = np.sqrt(np.sum(np.abs(Sxd) ** 2 / Sxx) / np.sum(Sdd))
        step = MU * np.clip((xi - DT_LOW) / (DT_HIGH - DT_LOW), 0.0, 1.0)

        px = np.abs(X[0]) ** 2
        power = px if power is None else 0.9 * power + 0.1 * px
        if step == 0 or np.dot(ref[sl], ref[sl]) < 1e-8:
            continue  # user talking, or nothing playing: don't learn from this block
        E = np.fft.rfft(np.concatenate([np.zeros(B), e]))
        G = np.conj(X) * E * (step / (P * power + 1e-3))
        g = np.fft.irfft(G, N, axis=1)
        g[:, B:] = 0  # gradient constraint -> linear (not circular) convolution
        W += np.fft.rfft(g, axis=1)
    return err, est, W


def _suppress_residual(err, est):
    """Spectral gain that knocks down echo the linear filter missed."""
    _, _, E = stft(err, RATE, nperseg=512)
    _, _, Y = stft(est, RATE, nperseg=512)
    gain = np.clip(1.0 - 1.5 * (np.abs(Y) ** 2) / (np.abs(E) ** 2 + 1e-10), 0.15, 1.0)
    _, out = istft(E * gain, RATE, nperseg=512)
    return out[:len(err)]


def cancel(audio, ref):
    """Remove `ref` playback from `audio` (sr.AudioData). Returns new AudioData."""
    if ref is None or audio.sample_width != 2:
        return audio
    if np.sqrt(np.mean(ref ** 2)) < SILENCE_RMS:
        return audio  # nothing playing

    mic = np.frombuffer(audio.frame_data, dtype=np.int16).astype(np.float32) / 32768.0
    mic = _resample(mic, audio.sample_rate, RATE)

    pre = len(ref) - len(mic)
    if pre < 0:
        return audio
    lag = _find_delay(mic, ref, pre)
    start = lag + GUARD  # reference must lead the mic so the filter stays causal
    aligned = ref[start:start + len(mic)]
    aligned = np.pad(aligned, (0, len(mic) - len(aligned)))

    # Two passes: the first lets the filter converge on this clip (starting from what
    # it learned on earlier clips - the room doesn't change), the second produces output.
    mic64, ref64 = mic.astype(np.float64), aligned.astype(np.float64)
    with _weights_lock:
        W = _weights[0]
    _, _, W = _nlms(mic64, ref64, W)
    err, est, W = _nlms(mic64, ref64, W)
    with _weights_lock:
        _weights[0] = W
    cleaned = _suppress_residual(err, est)
    cleaned = np.concatenate([cleaned, mic[len(cleaned):]])  # tail shorter than one block

    pcm = (np.clip(cleaned, -1, 1) * 32767).astype(np.int16).tobytes()
    return sr.AudioData(pcm, RATE, 2)


_recorder = LoopbackRecorder()
_weights = [None]               # adaptive filter carried between clips
_weights_lock = threading.Lock()


def start():
    return _recorder.start()


def reference(t_end, duration):
    """Snapshot of what was playing during a mic clip that ended at t_end (time.monotonic())."""
    return _recorder.window(t_end, duration)
