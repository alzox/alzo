import tkinter as tk
import components.data as data 
import queue

class UIManager:
    def __init__(self):
        self.root = tk.Tk()

        self.dot_index = 0
        self.animating = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.current_status_text = "initialized"  

        self._build_ui()
        self._setup_dragging()

        self.root.after(100, self.process_worker_status)


    def _build_ui(self):
        self.transparent = "#123456"

        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=self.transparent)
        self.root.attributes("-transparentcolor", self.transparent)

        self.container = tk.Frame(
            self.root,
            bg=self.transparent
        )
        self.container.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=0
        )


        self.status_label = tk.Label(
            self.container,
            text=self.current_status_text,
            fg="white",
            bg=self.transparent,
            font=("Consolas", 12),
            anchor="s",
            justify="center",
            wraplength=500,
            bd=0, 
            highlightthickness=0,
            padx=0,
            pady=0
        )
        self.status_label.pack(padx=0, pady=0)
        
    def _setup_dragging(self):
        """Make the borderless window draggable."""
        widgets = (
            self.root,
            self.container,
            self.status_label,
        )

        for widget in widgets:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

    def _start_drag(self, event):
        self._drag_offset_x = event.x_root - self.root.winfo_x()
        self._drag_offset_y = event.y_root - self.root.winfo_y()

    def _drag(self, event):
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def setup(self):
        self.root.update_idletasks()
        self.root.minsize(400,100)
        self.resize_to_content(center=True)

    def resize_to_content(self, center=True):
        self.root.update_idletasks()

        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()

        if center:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            x = (screen_width - width) // 2
            y = (screen_height - height) // 2

            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.root.geometry(f"{width}x{height}")

    def animation(self):
        """Start the dot animation until stop_animation() is called."""
        if not self.animating:
            self.animating = True
            self.dot_index = 0
            self.resize_to_content(False)
            self._animate_dots()

   
    def _animate_dots(self):
        if not self.animating:
            return

        dots = "." * (self.dot_index % 5)
        combined_text = f"{self.current_status_text}\n{dots}"
        self.status_label.config(text=combined_text)
        self.dot_index += 1

        self.resize_to_content(center=False)
        self.root.after(350, self._animate_dots)

    def set_status(self, text, color):
        self.current_status_text = text
        self.status_label.config(
            text=text,
            fg=color
        )

        self.root.update_idletasks()
        self.resize_to_content(center=False)

    def process_worker_status(self):
        try:
            message = data.ui.get_nowait()
            command = message[0]
            value = message[1] if len(message) > 1 else None

            if command == "start":
                self.animation()

            elif command == "recognized":
                self.set_status(value, "gray")

            elif command == "executed":
                self.set_status(value, "white")

            elif command == "close":
                self.root.destroy()
                return

            data.ui.task_done()
        except queue.Empty:
           pass

        self.root.after(100, self.process_worker_status)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ui = UIManager()
    data.ui.put(("start",))
    ui.run()
