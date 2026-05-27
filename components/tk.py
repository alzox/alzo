import threading
import tkinter as tk
from tkinter import ttk
import time

X_OFFSET = 1350
Y_OFFSET = 350

def make_message_box(message):
    def show_box():
        # Root Configs
        root = tk.Tk()
        root.title("alzo")
        root.attributes("-topmost", True)
        root.resizable(False, False)
        root.overrideredirect(False)

        # Message Box
        label = tk.Label(root, text=message, padx=20, pady=20, justify="left", wraplength=750, anchor="center") #wrap is kind of magic, but max-width of your monitor
        label.pack()

        # Placement
        x,y = get_middle(root)
        root.geometry(f"+{x}+{y}")

        root.mainloop()
    # show_box()
    threading.Thread(target=show_box, daemon=True).start()

def make_progress_bar(duration=5):
    def show_bar():
        # Root Configs
        root = tk.Tk()
        root.title("Listening...")
        root.attributes("-topmost", True)
        root.resizable(False, False)
        root.configure(bg="black")
        root.overrideredirect(True)

        # Label 
        label = tk.Label(
                root,
                text="Listening...",
                fg="white",
                bg="black",   
                font=("Segoe UI", 14)
                )
        label.pack(pady=10)

        # Progress Bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
                "Clean.Horizontal.TProgressbar",
                troughcolor="black",   # must match window bg
                background="white",  # bar color
                bordercolor="black",
                lightcolor="white",
                darkcolor="white",
                relief="flat",
                throughrelief="flat",
                borderwidth=0
                )
        progress = ttk.Progressbar(
                root,
                style="Clean.Horizontal.TProgressbar",
                orient="horizontal",
                length=500,
                mode="determinate"
                )
        progress.pack()
        root.update_idletasks()

        # Custom Offsets
        x = -650
        y = 450
        root.geometry(f"{600}x{120}+{x}+{y}")

        # Animate
        steps = 100
        delay = duration / steps

        for i in range(steps + 1):
            progress["value"] = i
            root.update()
            time.sleep(delay)

        root.destroy()
    # show_bar()
    threading.Thread(target=show_bar, daemon=True).start()

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
