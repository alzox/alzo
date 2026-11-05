import threading
import inspect
import re

import numpy as np
from faster_whisper import WhisperModel

import components.data as data
import components.echo as echo
from components.commands import COMMANDS

# from langchain.agents import create_agent
# from langchain_mistralai import ChatMistralAI
# MISTRAL = ChatMistralAI(model="mistral-small-2503", temperature=.7) # pyright: ignore
# SYSTEM_PROMPT = """You are a helpful AI assistant meant to answer questions and call tools as a desktop assistant."""
# AGENT = create_agent(model = MISTRAL, tools=agent.TOOLS, system_prompt=SYSTEM_PROMPT)

def action(command):
    for keywords, func in COMMANDS.items():
        command_words = command.split()
        contains_all = all((word in command_words for word in keywords))
        if contains_all:
            data.ui.put(("executed", command))
            sig = inspect.signature(func)
            params = sig.parameters
            if len(params) == 0:
                func()
            else:
                func(command)
    return 0

from components.listener import WAKE_WORD
_model = None
_model_lock = threading.Lock()

def get_model():
    # faster-whisper (CTranslate2, int8) is a lot lighter than openai-whisper for the same base.en weights
    global _model
    with _model_lock:
        if _model is None:
            _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model

def transcribe(audio):
    pcm = np.frombuffer(audio.get_raw_data(convert_rate=16000, convert_width=2), dtype=np.int16)
    segments, _ = get_model().transcribe(pcm.astype(np.float32) / 32768.0, language="en", beam_size=1)
    text = " ".join(seg.text for seg in segments)
    text = re.sub(r"[^\w\s]", "", text.lower()).split()
    if WAKE_WORD in text[:3]:  # the clip starts with the wake word; drop it
        text = text[text.index(WAKE_WORD) + 1:]
    return " ".join(text)

def worker():
    while True:
        item = data.audio.get()
        if item is None:
            break

        try:
            audio, ref = item
            audio = echo.cancel(audio, ref)  # strip computer playback picked up by the mic
            command = transcribe(audio)
            if command != "":
                data.ui.put(("recognized",command))
                action(command)
            else:
                data.ui.put(("idle",))  # heard nothing usable; go back to waiting
        except Exception as e:
            print(e)
            data.ui.put(("idle",))
    
        data.audio.task_done()

def start_workers():
    # commands only arrive after the wake word, so one worker is plenty
    get_model()
    threading.Thread(target=worker, daemon=True).start()

def submit_audio(audio, ref=None):
    if audio is None:
        return
    data.audio.put((audio, ref))

