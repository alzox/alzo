import tkinter as tk
import components.data as data 
import queue

HIDE_AFTER_MS = 2000  # how long a recognized command stays on screen
IDLE_TEXT = 'say "command"'
MAX_DOTS = 3          # dot animation cycles "", ".", "..", "..."
DOT_INTERVAL_MS = 350

class UIManager:
    def __init__(self):
        self.root = tk.Tk()

        self.dot_index = 0
        self.animating = False
        self._dots_job = None
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.current_status_text = "initialized"
        self._hide_job = None

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
            side="left",
            fill="both",
            expand=True,
            pady=0
        )
 
        self.status_label = tk.Label(
            self.container,
            text=self.current_status_text,
            fg="white",
            bg=self.transparent,
            font=("Consolas", 16),
            anchor="s",
            justify="center",
            bd=0,
            highlightthickness=0,
            padx=0,
            pady=0
        )
        # packed (not placed) so the window's requested width follows the text:
        # the message stays on one line and the window widens to fit it
        self.status_label.pack(padx=20, pady=(20, 0))

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
        else:
            # grow/shrink around the current horizontal center instead of off the right edge
            width = max(width, self.root.minsize()[0])
            x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
            y = self.root.winfo_y()

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def animation(self):
        """Animate dots after the current status until stop_animation() is called."""
        self.stop_animation()
        self.animating = True
        self.dot_index = 0
        self._animate_dots()

    def stop_animation(self):
        self.animating = False
        if self._dots_job is not None:
            self.root.after_cancel(self._dots_job)
            self._dots_job = None
        self.status_label.config(text=self.current_status_text)

    def _animate_dots(self):
        if not self.animating:
            return

        # same line as the text, padded to a fixed width so the text doesn't shift
        dots = "." * (self.dot_index % (MAX_DOTS + 1))
        self.status_label.config(text=f"{self.current_status_text}{dots:<{MAX_DOTS}}")
        self.dot_index += 1

        self.resize_to_content(center=False)
        self._dots_job = self.root.after(DOT_INTERVAL_MS, self._animate_dots)

    def set_status(self, text, color):
        text = " ".join(str(text).split())  # always a single line
        self.current_status_text = text
        self.status_label.config(
            text=text,
            fg=color
        )

        self.root.update_idletasks()
        self.resize_to_content(center=False)

    def _schedule_hide(self, delay_ms=HIDE_AFTER_MS):
        """Clear the message after delay_ms; restarts the timer if one is pending."""
        self._cancel_hide()
        self._hide_job = self.root.after(delay_ms, self._hide)

    def _cancel_hide(self):
        if self._hide_job is not None:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None

    def _hide(self):
        self._hide_job = None
        self._idle()

    def _idle(self):
        """Back to waiting for the wake word."""
        self.stop_animation()
        self.set_status(IDLE_TEXT, "gray")

    def process_worker_status(self):
        try:
            message = data.ui.get_nowait()
            command = message[0]
            value = message[1] if len(message) > 1 else None

            if command == "start":
                self.animation()

            elif command == "idle":
                self._cancel_hide()
                self._idle()

            elif command == "wake":
                self._cancel_hide()
                self.set_status("listening", "white")
                self.animation()

            elif command == "recognized":
                self.stop_animation()
                self.set_status(value, "gray")
                self._schedule_hide()

            elif command == "executed":
                self.stop_animation()
                self.set_status(value, "white")
                self._schedule_hide()

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
