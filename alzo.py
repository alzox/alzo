import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()

import components.tk as tk
import components.sound as sound
import components.worker as worker

# init
r = sr.Recognizer()
m = sr.Microphone()
r.pause_threshold = .5                      # How long to wait before considering speech ended
r.phrase_threshold = .3                     # Minimum audio length to consider as speech
with m as source: r.adjust_for_ambient_noise(source, duration=3)

worker.start_worker()

while True:
    with m as source:
        # dispatch listening animation
        tk.make_progress_bar(2)
        audio = r.record(source, duration=2)
    worker.submit_audio(audio)

