from dotenv import load_dotenv

load_dotenv()

import components.tk as tk
import components.worker as worker
import components.echo as echo
from components.listener import Listener

# init
ui = tk.UIManager()

# start all the threads
echo.start()                          # records speaker output for echo cancellation
worker.start_workers()                # whisper: turns command clips into text + actions
Listener(worker.submit_audio).start() # vosk: waits for the wake word, records the command
ui.setup()
ui.run()
