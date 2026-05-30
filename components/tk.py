import threading
import tkinter as tk
from tkinter import ttk
import time

X_OFFSET = 1350
Y_OFFSET = 350

class UIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # hide initially

        self.current = None  # "box" | "bar"
        self.container = None

    # --------- CORE CONTROL ---------
    def teardown(self):
        if self.container:
            self.container.destroy()
            self.container = None
        self.current = None

    # --------- MESSAGE BOX ---------
    def setup_box(self, message):
        self.teardown()
        self.current = "box"

        self.root.deiconify()
        self.root.title("alzo")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(False)
        self.root.configure(bg="white")

        self.container = tk.Frame(self.root, bg="white")
        self.container.pack()

        label = tk.Label(
            self.container,
            text=message,
            padx=20,
            pady=20,
            wraplength=750,
            justify="left",
            bg="white"
        )
        label.pack()

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 300
        y = (self.root.winfo_screenheight() // 2) - 100
        self.root.geometry(f"+{x}+{y}")

    # --------- PROGRESS BAR ---------
    def setup_bar(self, duration=5):
        self.teardown()
        self.current = "bar"

        self.root.deiconify()
        self.root.title("Listening...")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.configure(bg="black")
        self.root.overrideredirect(True)

        self.container = tk.Frame(self.root, bg="black")
        self.container.pack(fill="both", expand=True)

        label = tk.Label(
            self.container,
            text="Listening...",
            fg="white",
            bg="black",
            font=("Segoe UI", 14)
        )
        label.pack(pady=10)

        progress = ttk.Progressbar(
            self.container,
            orient="horizontal",
            length=500,
            mode="determinate"
        )
        progress.pack()

        # position
        self.root.geometry("600x120+-650+450")

        # animate in background
        def animate():
            steps = 100
            delay = duration / steps

            for i in range(steps + 1):
                if self.current != "bar":
                    return
                progress["value"] = i
                time.sleep(delay)

            self.root.withdraw()
            self.current = None

        threading.Thread(target=animate, daemon=True).start()

# Singleton
ui = UIManager()


# --------- PUBLIC FUNCTIONS ---------
def run_on_ui_thread(func, *args):
    ui.root.after(0, func, *args)

def make_message_box(message):
    ui.setup_box(message)

def make_progress_bar(duration=5):
    ui.setup_bar(duration)

def get_middle(root):
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2) + X_OFFSET # Magic number, but meant to move if you have multiple monitors
    y = (screen_height // 2) - (height // 2) + Y_OFFSET # Same as above, XY starts at 0,0 top-left of screen
    return x,y

def get_mouse_position():
    root = tk.Tk()
    root.withdraw()
    x = root.winfo_pointerx()
    y = root.winfo_pointery()
    root.destroy()
    return x, y

if __name__ == "__main__":
    make_progress_bar(2)
    while True:
        print(get_mouse_position())
        time.sleep(1)
