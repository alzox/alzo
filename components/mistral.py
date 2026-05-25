import os
import re
import sys
from dotenv import load_dotenv
load_dotenv()

from mistralai import Mistral
import subprocess

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-2503"
def markdown_to_ansi(text):
    """Convert basic Markdown to ANSI color codes for PowerShell"""
    # Headers
    text = re.sub(r'^# (.*?)$', r'\033[1;34m\1\033[0m', text, flags=re.MULTILINE)  # Blue bold
    text = re.sub(r'^## (.*?)$', r'\033[1;36m\1\033[0m', text, flags=re.MULTILINE)  # Cyan bold
    text = re.sub(r'^### (.*?)$', r'\033[1;32m\1\033[0m', text, flags=re.MULTILINE)  # Green bold
    
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', text)
    
    # Italic (show as underline since italic isn't well supported)
    text = re.sub(r'\*(.*?)\*', r'\033[4m\1\033[0m', text)
    
    # Code blocks
    text = re.sub(r'`([^`]+)`', r'\033[43;30m \1 \033[0m', text)  # Yellow background
    
    # Code blocks (triple backticks)
    text = re.sub(r'```(.*?)```', r'\033[100;37m\1\033[0m', text, flags=re.DOTALL)
    
    return text

def clean_markdown(text):
    """Strip Markdown formatting for plain text output"""
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove code formatting
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'```(.*?)```', r'\1', text, flags=re.DOTALL)
    
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text

client = Mistral(api_key=api_key)
system_prompt = """You are a helpful assistant. Please format your responses in clean, readable text.
Use minimal markdown - only use **bold** for emphasis and `code` for technical terms.
Avoid complex formatting, tables, or extensive markdown since this will be displayed in a terminal."""

def question(text):
    """Ask a question to the Mistral AI model and return the response."""
    stream = client.chat.stream(
        model=model,
        messages=[
            {"role": "user", "content": text},
            {"role": "system", "content": system_prompt}
        ]
    )
    return stream 

def process_question(question_text):
    print(f"\nAsking Mistral: {str.title(question_text)}")
    print("-" * 50)
    
    
    try:
        response = question(question_text)
        full_response = ""
        
        for chunk in response:
            if chunk.data.choices[0].delta.content:
                content = chunk.data.choices[0].delta.content
                full_response += content
                print(markdown_to_ansi(content), end="", flush=True)
                
        print("\n" + "-" * 50)
        print("Response complete.")
        print("Ask another question or Enter to exit.")
        q = input()
        if q: process_question(q)
        
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        print("Press Enter to continue or X to exit")
        input()

def call_mistral_with_question(full_command):
    question_text = full_command.replace("question", "").strip()
    if question_text:
        mistral_path = os.path.join(os.path.dirname(__file__), "mistral.py")
        subprocess.Popen([
            "python", mistral_path, question_text
        ], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        print("No question detected after 'question' command")

if __name__ == "__main__":
    if len(sys.argv) > 1: # RUNS AS A NEW PROCESS
        print(sys.argv)
        question_text = " ".join(sys.argv[1:])
        process_question(question_text)
    else:
        process_question()