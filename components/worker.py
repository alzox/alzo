import speech_recognition as sr
import threading 
import inspect

import components.agent as agent
import components.data as data
from components.commands import COMMANDS

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
MISTRAL = ChatMistralAI(model="mistral-small-2503", temperature=.7) # pyright: ignore
SYSTEM_PROMPT = """You are a helpful AI assistant meant to answer questions and call tools as a desktop assistant."""
AGENT = create_agent(model = MISTRAL, tools=agent.TOOLS, system_prompt=SYSTEM_PROMPT)

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

def worker():
    r = sr.Recognizer()  
    while True:
        audio = data.audio.get()
        if audio is None:
            break

        try:
            command = r.recognize_google(audio).lower().replace(".","").strip() # pyright: ignore
            data.ui.put(("recognized",command))
            if command != "":
                action(command)
        except Exception:
            pass
    
        data.audio.task_done()

def start_worker():
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread

def start_workers():
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

def submit_audio(audio):
    if audio is None:
        return
    data.audio.put(audio)

