import speech_recognition as sr
import threading 
import queue

import components.agent as agent
import components.tk as tk

from components.commands import COMMANDS

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI


# Tools are just fed in as model input, try removing tools and seeing prompt tokens.
print("Setting Up Agent")
MISTRAL = ChatMistralAI(model="mistral-small-2503", temperature=.7)
SYSTEM_PROMPT = """You are a helpful AI assistant meant to answer questions and call tools as a desktop assistant."""
AGENT = create_agent(model = MISTRAL, tools=agent.TOOLS, system_prompt=SYSTEM_PROMPT)
print("Agent Set-up!")

audio_queue = queue.Queue()

def action(command):
    for keywords, func in COMMANDS.items():
        command_words = command.replace(".","").split()
        contains_all = all((word in command_words for word in keywords))
        if contains_all:
            print(f"Executing command: {keywords}")
            func(command)
            return

        if len(command_words) >= 5: # Don't want this running for random pick-ups
            result = AGENT.invoke({"messages": [{"role": "user", "content": f"{command}"}]})
            if result['messages'][-1].content.replace(".","") != "Nothing":
                tk.make_message_box(result['messages'][-1].content.replace("*",""))
    return

def whisper_worker():
    print("[Worker] Started")
    r = sr.Recognizer()  
    while True:
        audio = audio_queue.get()

        if audio is None:
            break
        try:
            word = r.recognize_whisper(audio).lower().strip().replace(".","")
            if word != "": print(word)
        except Exception as e:
            print("[Worker Error]:", e)

        audio_queue.task_done()

def start_worker():
    thread = threading.Thread(target=whisper_worker, daemon=True)
    thread.start()
    return thread

def submit_audio(audio):
    audio_queue.put(audio)
