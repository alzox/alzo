import os
import keyboard
from multiprocessing import Process

import components.command.mistral as mistral
import components.command.win32 as win32
import components.command.sound as sound

COMMANDS = {
    # MISC
    ("hate", "game"): lambda: keyboard.send('alt+f4'),
    ("clip", "that"): lambda: print("Making a clip..."),
    
    # WINDOWS
    ("lock", "computer"): lambda: os.system("rundll32.exe user32.dll,LockWorkStation"),
    ("shut", "down", "computer"): lambda: os.system("shutdown /s /t 1"),
    ("restart", "computer"): lambda: os.system("shutdown /r /t 1"),
    
    # OPEN/CLOSE COMMANDS
    ("open", "chrome"): lambda: os.system("start chrome"),
    ("close", "chrome"): lambda: os.system("taskkill /f /im chrome.exe"),
    ("open", "notepad"): lambda: os.system("notepad"),
    ("close", "notepad"): lambda: os.system("taskkill /f /im notepad.exe"),
    ("open", "code"): lambda: os.system("code"),
    ("close", "code"): lambda: os.system("taskkill /f /im Code.exe"),
    ("open", "habitica"): lambda: os.system(r'start "" "https://habitica.com"'),
    ("close", "habitica"): lambda: print("Habitica is a web app, no process to close."),
    ("open", "spotify"): lambda: os.system("start spotify"),
    ("close", "spotify"): lambda: os.system("taskkill /f /im Spotify.exe"),
    ("open", "discord"): lambda: os.system("start discord"),
    ("close", "discord"): lambda: os.system("taskkill /f /im Discord.exe"),
    ("open", "steam"): lambda: os.system("start steam"),
    ("close", "steam"): lambda: os.system("taskkill /f /im Steam.exe"),
    
    # GOTOs 
    ("go", "to", "chrome"): lambda: win32.make_window_active("Google Chrome"),
    ("go", "to", "notepad"): lambda: win32.make_window_active("Notepad"),
    ("go", "to", "code"): lambda: win32.make_window_active("Visual Studio Code"),
    ("go", "to", "spotify"): lambda: win32.make_window_active("Spotify"),
    ("go", "to", "discord"): lambda: win32.make_window_active("Discord"),
    ("go", "to", "steam"): lambda: win32.make_window_active("Steam"),
    
    # GOOGLE CHROME
    ("google",): lambda command: os.system(rf'start "" "https://www.google.com/search?q={command}"') if not command == "google" and command.startswith("google") else None,

    # SPOTIFY (Requires Premium) 
    # ("play", "music"): lambda: spotify.play_pause(),
    # ("pause", "music"): lambda: spotify.play_pause(),
    # ("stop", "music"): lambda: spotify.play_pause(),
    # ("next", "song"): lambda: spotify.next_track(),
    # ("skip", "song"): lambda: spotify.next_track(),
    # ("previous", "song"): lambda: spotify.previous_track(),
    # ("last", "song"): lambda: spotify.previous_track(),
    # ("spotify","play", "by"): lambda: spotify.play_artist_song(command.split("by ")[1].strip(), command.split("play ")[1].split(" by ")[0].strip()),
    # ("spotify","play",): lambda: spotify.play_artist(command.replace("play ", "")),
    # ("clear", "q"): lambda: spotify.clear_queue(),
    
    # SOUND
    ("play","sound"): lambda: sound.play_pause(),
    ("pause","sound"): lambda: sound.play_pause(),
    ("volume", "up"): lambda: sound.volume_up(),
    ("volume", "down"): lambda: sound.volume_down(),
    ("mute", "sound"): lambda: sound.mute(),
    ("mute",): lambda: sound.mute(),

    # MISTRAL
    ("question",): lambda command: mistral.open_mistral(command), 
    ("open", "chat"): lambda command: mistral.open_mistral()
}

if __name__ == "__main__":
    mistral.open_mistral("QUESTION HERE")
