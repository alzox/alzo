"""
Always-on wake word listener.

A small Vosk model (~40 MB, streaming, CPU) runs on the live mic stream and watches
for WAKE_WORD. When it hears it, we record until the user's sentence ends
and hand that clip (plus what the speakers played meanwhile, for echo cancellation)
to the worker, which runs the heavier Whisper model on it.
"""
import collections
import json
import os
import threading
import time

import pyaudio
import speech_recognition as sr
from vosk import KaldiRecognizer, Model, SetLogLevel

import components.data as data
import components.echo as echo

WAKE_WORD = "command"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "vosk-model-small-en-us-0.15")

RATE = 16000
CHUNK = RATE // 10       # 100 ms reads
PRE_ROLL = 1.0           # seconds kept from before the wake word fired ("command open spotify" in one breath)
WAIT_FOR_SPEECH = 8.0    # after a bare wake word, give up if nothing else is said for this long
MAX_COMMAND = 15.0       # hard cap on a command recording (wake word + pause + command)

SetLogLevel(-1)


def _words(result, key):
    return json.loads(result).get(key, "").split()


def _after_wake(words):
    """Words following the last wake word (all of them if there is none)."""
    if WAKE_WORD not in words:
        return words
    return words[len(words) - words[::-1].index(WAKE_WORD):]


class Listener:
    def __init__(self, submit):
        self.submit = submit
        self.model = Model(os.path.abspath(MODEL_PATH))

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    # -- mic ---------------------------------------------------------------
    def _run(self):
        while True:
            p = pyaudio.PyAudio()
            try:
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                                input=True, frames_per_buffer=CHUNK)
                print("mic connected")
                self._listen(stream)
            except OSError as e:
                print(f"Microphone disconnected; reconnecting: {e}")
                time.sleep(1)
            finally:
                p.terminate()

    def _read(self, stream):
        return stream.read(CHUNK, exception_on_overflow=False)

    # -- wake word ---------------------------------------------------------
    def _listen(self, stream):
        # Full small-model vocabulary rather than a one-word grammar: with a grammar, any
        # speech gets forced onto the wake word. Here other words compete, so "commander",
        # "come on", etc. don't trigger it. Costs ~20% of one CPU core in real time.
        rec = KaldiRecognizer(self.model, RATE)
        recent = collections.deque(maxlen=int(PRE_ROLL * RATE / CHUNK))
        data.ui.put(("idle",))
        while True:
            chunk = self._read(stream)
            recent.append(chunk)

            final = rec.AcceptWaveform(chunk)
            heard = _words(rec.Result(), "text") if final else _words(rec.PartialResult(), "partial")

            if WAKE_WORD in heard:
                if not self._record_command(stream, rec, list(recent), _after_wake(heard), final):
                    data.ui.put(("idle",))  # nothing said after the wake word
                recent.clear()
                rec.Reset()

    # -- command -----------------------------------------------------------
    def _record_command(self, stream, rec, frames, after, utterance_done):
        """Keep recording until Vosk says the sentence holding the command has ended.
        Returns False if nothing followed the wake word (no clip submitted)."""
        data.ui.put(("wake",))
        elapsed = 0.0
        while not (utterance_done and after):  # done once a sentence ends with words after "command"
            if not after and elapsed >= WAIT_FOR_SPEECH:
                return False  # just "command" and then nothing
            if elapsed >= MAX_COMMAND:
                break
            chunk = self._read(stream)
            frames.append(chunk)
            elapsed += CHUNK / RATE

            utterance_done = rec.AcceptWaveform(chunk)
            heard = _words(rec.Result(), "text") if utterance_done else _words(rec.PartialResult(), "partial")
            after = _after_wake(heard)

        t_end = time.monotonic()
        audio = sr.AudioData(b"".join(frames), RATE, 2)
        ref = echo.reference(t_end, len(audio.frame_data) / 2 / RATE)
        self.submit(audio, ref)  # the worker updates the UI once it has a result
        return True
