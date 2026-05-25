
import win32gui
import win32con
import threading

# NEED TO REFACTOR WOW THIS IS BAD

def make_window_active(window_name):
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            windows.append(win32gui.GetWindowText(hwnd))
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    print("Active windows:")
    for w in windows:
        print(f"- {w}")
    
    hwnd = win32gui.FindWindowEx(None, None, None, window_name)
    
    if not hwnd:
        def find_window_callback(hwnd, param):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_name.lower() in window_title.lower():
                    param.append(hwnd)
        
        found_windows = []
        win32gui.EnumWindows(find_window_callback, found_windows)
        if found_windows:
            hwnd = found_windows[0]  # Use the first match
    
    if hwnd:
        window_title = win32gui.GetWindowText(hwnd)
        print(f"Found window: {window_title}")
        
        try:
            # Simple approach that works better with tiling window managers
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(hwnd)
            
            try:
                win32gui.SetForegroundWindow(hwnd)
            except:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            print(f"Activated window via Windows API: {window_title}")
            
        except Exception as e:
            print(f"Error activating window: {e}")
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                print(f"Made window visible (final fallback): {window_title}")
            except Exception as e2:
                print(f"All methods failed: {e2}")
    else:
        print(f"Window containing '{window_name}' not found.")
        
def make_message_box(message):
    threading.Thread(
        target=lambda: win32gui.MessageBox(None, message, "alzo", 0),
        daemon=True
    ).start()