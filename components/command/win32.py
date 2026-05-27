import win32gui
import threading

def callback(hwnd, windows):
    title = win32gui.GetWindowText(hwnd)
    if win32gui.IsWindowVisible(hwnd) and title:
        windows.append({"hwnd": hwnd, "title": title})
        return 

def make_window_active(window_name):
    windows = []
    win32gui.EnumWindows(callback, windows)
    for w in windows:
        if window_name in w["title"].lower():
            win32gui.SetForegroundWindow(w["hwnd"])
            return
       
def make_message_box(message):
    threading.Thread(
        target=lambda: win32gui.MessageBox(None, message, "alzo", 0),
        daemon=True
    ).start()

if __name__ == "__main__":
    make_window_active("chrome")

