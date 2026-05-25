import time
import ctypes
import threading
from playsound import playsound
import os

# VIRTUAL KEY CODES
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD
KEYEVENTF_KEYUP = 0x0002

def send_key(vk_code):
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        return True
    except Exception as e:
        print(f"Error sending key: {e}")
        return False

def play_pause():
    send_key(VK_MEDIA_PLAY_PAUSE)

def next_track():
    send_key(VK_MEDIA_NEXT_TRACK)

def previous_track():
    send_key(VK_MEDIA_PREV_TRACK)

def volume_up():
    for i in range(5):
        send_key(VK_VOLUME_UP)

def volume_down():
    for i in range(5):
        send_key(VK_VOLUME_DOWN)

def mute():
    send_key(VK_VOLUME_MUTE)
    
def activate():
    mp3_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'activated.mp3')
    threading.Thread(target=lambda: playsound(mp3_path), daemon=True).start()