import speech_recognition as sr
import threading 
import queue
import inspect

import components.agent as agent
import components.tk as tk

from components.commands import COMMANDS

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
MISTRAL = ChatMistralAI(model="mistral-small-2503", temperature=.7) # pyright: ignore
SYSTEM_PROMPT = """You are a helpful AI assistant meant to answer questions and call tools as a desktop assistant."""
AGENT = create_agent(model = MISTRAL, tools=agent.TOOLS, system_prompt=SYSTEM_PROMPT)

audio_queue = queue.Queue()

def action(command):
    for keywords, func in COMMANDS.items():
        command_words = command.split()
        contains_all = all((word in command_words for word in keywords))
        if contains_all:
            print(f"Executing command: {keywords}")
            sig = inspect.signature(func)
            params = sig.parameters

            if len(params) == 0:
                func()
            else:
                func(command)
        # Not sure how I want this to work, maybe set a flag so shows don't invoke it, or better prompting/reviewing the prompting
        # if len(command_words) >= 10: # Don't want this running for random pick-ups
        #     result = AGENT.invoke({"messages": [{"role": "user", "content": f"{command}"}]})
        #     if result['messages'][-1].content.replace(".","") != "Nothing":
        #         tk.make_message_box(result['messages'][-1].content.replace("*",""))
    return 0

def worker():
    print("Worker Started")
    r = sr.Recognizer()  
    while True:
        audio = audio_queue.get()
        if audio is None:
            break

        try:
            command = r.recognize_google(audio).lower().replace(".","").strip() # pyright: ignore
            if command != "":
                print(command)
                action(command)
        except Exception as e:
            print("[ERROR]")
    
        audio_queue.task_done()

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
    audio_queue.put(audio)
