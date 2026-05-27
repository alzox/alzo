import os
import re
import sys
from dotenv import load_dotenv
load_dotenv()

from mistralai import Mistral
import subprocess

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
system_prompt = """You are a helpful assistant. Please format your responses in clean, readable text.
Use minimal markdown - only use **bold** for emphasis and `code` for technical terms.
Avoid complex formatting, tables, or extensive markdown since this will be displayed in a terminal."""
model = "mistral-small-2503"
def markdown_to_ansi(text):
    text = re.sub(r'^# (.*?)$', r'\033[1;34m\1\033[0m', text, flags=re.MULTILINE)       # H1
    text = re.sub(r'^## (.*?)$', r'\033[1;36m\1\033[0m', text, flags=re.MULTILINE)      # H2
    text = re.sub(r'^### (.*?)$', r'\033[1;32m\1\033[0m', text, flags=re.MULTILINE)     # H3
    text = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', text)                          # Bold
    text = re.sub(r'\*(.*?)\*', r'\033[4m\1\033[0m', text)                              # Italic
    text = re.sub(r'`([^`]+)`', r'\033[43;30m \1 \033[0m', text)                        # []
    text = re.sub(r'```(.*?)```', r'\033[100;37m\1\033[0m', text, flags=re.DOTALL)      # Code Blocks
    return text

def ask_question(messages):
    response = client.chat.complete(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def ask_mistral(question = ""):
    context = [
        {"role": "system", "content": system_prompt}
    ]
    while True:
        if not question: question_text = input("\nAsk Mistral (Enter to exit): ").strip()
        else:
            question_text = question
            question = None

        if not question_text:
            print("Goodbye!")
            break

        print(f"\nAsking Mistral: {question_text.title()}")
        print("-" * 50)

        try:
            context.append({"role": "user", "content": question_text})
            answer = ask_question(context)
            context.append({"role": "assistant", "content": answer})
            print(markdown_to_ansi(answer))

            print("-" * 50)
            print("Response complete.")

        except Exception as e:
            print(f"\nError calling Mistral API: {e}")
            print("Try again.")

def open_mistral(question = ""):
    subprocess.Popen(
        f'start "" /max cmd /k "{sys.executable} {os.path.join(os.path.dirname(__file__), "mistral.py")} {question}"',
        shell=True
    )


if __name__ == "__main__":
    if len(sys.argv) > 1: # RUNS AS A NEW PROCESS
        question_text = " ".join(sys.argv[1:])
        ask_mistral(question_text)
    else:
        ask_mistral("TEST")

