import threading
import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()

import components.tk as tk
import components.worker as worker
import components.data as data

DURATION = 2

# init
ui = tk.UIManager()
r = sr.Recognizer()
m = sr.Microphone()
r.pause_threshold = .5                      # How long to wait before considering speech ended
r.phrase_threshold = .3                     # Minimum audio length to consider as speech
with m as source: r.adjust_for_ambient_noise(source, duration=3)

def listen():
    while True:
        with m as source:
            data.ui.put(("start",))
            audio = r.record(source, duration=DURATION)
        worker.submit_audio(audio)

# start all the threads
threading.Thread(target=listen, daemon=True).start()
worker.start_workers()
ui.setup()
ui.run()
