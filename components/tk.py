import threading
import tkinter as tk
from tkinter import ttk
import time

def make_message_box(message):
    def show_box():
        root = tk.Tk()
        root.title("alzo")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        label = tk.Label(root, text=message, padx=20, pady=20, justify="left", wraplength=750, anchor="center") #wrap is kind of magic, but max-width of your monitor
        label.pack()
        
        x,y = get_middle(root)
        root.geometry(f"+{x}+{y}")

        root.overrideredirect(False)
        root.mainloop()
    show_box()
    # threading.Thread(target=show_box, daemon=True).start()

def make_progress_bar(duration=5):
    def show_bar():
        root = tk.Tk()
        # root.attributes("-alpha", 0.7)
        root.title("Listening...")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        # Optional overlay style
        root.overrideredirect(True)
        root.configure(bg="black")
        root.wm_attributes("-transparentcolor", "black")

        # Container frame (gives padding + structure)
        frame = tk.Frame(root)
        frame.pack(pady=10)

        # Label 
        label = tk.Label(
            root,
            text="Listening...",
            fg="white",
            bg="black",   
            font=("Segoe UI", 14)
            )
        label.pack()

        # Progress bar
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

        # x,y are found by running the helper script
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
    
def get_middle(root: tk):
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2) + 1350 # Magic number, but meant to move if you have multiple monitors
    y = (screen_height // 2) - (height // 2) + 350 # Same as above, X,Y starts at 0,0 top-left of screen
    return x,y
 
# Helps place root.geometry to where you want it    
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
