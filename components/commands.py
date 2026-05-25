import os
import keyboard

import components.mistral as mistral
import components.win32 as win32
import components.spotify as spotify
import components.sound as sound


COMMANDS = {
    # MISC
    ("hate", "game"): lambda command: keyboard.send('alt+f4'),
    ("clip", "that"): lambda command: print("Making a clip..."),
    
    # WINDOWS
    ("lock", "computer"): lambda command: os.system("rundll32.exe user32.dll,LockWorkStation"),
    ("shut", "down", "computer"): lambda command: os.system("shutdown /s /t 1"),
    ("restart", "computer"): lambda command: os.system("shutdown /r /t 1"),
    
    # OPEN/CLOSE COMMANDS
    ("open", "chrome"): lambda command: os.system("start chrome"),
    ("close", "chrome"): lambda command: os.system("taskkill /f /im chrome.exe"),
    ("open", "notepad"): lambda command: os.system("notepad"),
    ("close", "notepad"): lambda command: os.system("taskkill /f /im notepad.exe"),
    ("open", "code"): lambda command: os.system("code"),
    ("close", "code"): lambda command: os.system("taskkill /f /im Code.exe"),
    ("open", "habitica"): lambda command: os.system(r'start "" "https://habitica.com"'),
    ("close", "habitica"): lambda command: print("Habitica is a web app, no process to close."),
    ("open", "spotify"): lambda command: os.system("start spotify"),
    ("close", "spotify"): lambda command: os.system("taskkill /f /im Spotify.exe"),
    ("open", "discord"): lambda command: os.system("start discord"),
    ("close", "discord"): lambda command: os.system("taskkill /f /im Discord.exe"),
    ("open", "steam"): lambda command: os.system("start steam"),
    ("close", "steam"): lambda command: os.system("taskkill /f /im Steam.exe"),
    
    # GOTOs 
    ("go", "to", "chrome"): lambda command: win32.make_window_active("Google Chrome"),
    ("go", "to", "notepad"): lambda command: win32.make_window_active("Notepad"),
    ("go", "to", "code"): lambda command: win32.make_window_active("Visual Studio Code"),
    ("go", "to", "spotify"): lambda command: win32.make_window_active("Spotify"),
    ("go", "to", "discord"): lambda command: win32.make_window_active("Discord"),
    ("go", "to", "steam"): lambda command: win32.make_window_active("Steam"),
    
    # GOOGLE CHROME
    ("google",): lambda command: os.system(rf'start "" "https://www.google.com/search?q={command}"') if not command == "google" and command.startswith("google") else None,

    # SPOTIFY (Requires Premium) 
    # ("play", "music"): lambda command: spotify.play_pause(),
    # ("pause", "music"): lambda command: spotify.play_pause(),
    # ("stop", "music"): lambda command: spotify.play_pause(),
    # ("next", "song"): lambda command: spotify.next_track(),
    # ("skip", "song"): lambda command: spotify.next_track(),
    # ("previous", "song"): lambda command: spotify.previous_track(),
    # ("last", "song"): lambda command: spotify.previous_track(),
    # ("spotify","play", "by"): lambda command: spotify.play_artist_song(command.split("by ")[1].strip(), command.split("play ")[1].split(" by ")[0].strip()),
    # ("spotify","play",): lambda command: spotify.play_artist(command.replace("play ", "")),
    # ("clear", "q"): lambda command: spotify.clear_queue(),
    
    # SOUND
    ("play","sound"): lambda command: sound.play_pause(),
    ("pause","sound"): lambda command: sound.play_pause(),
    ("volume", "up"): lambda command: sound.volume_up(),
    ("volume", "down"): lambda command: sound.volume_down(),
    ("mute", "sound"): lambda command: sound.mute(),
    ("mute",): lambda command: sound.mute(),

    # MISTRAL
    # ("question",): lambda command: mistral.call_mistral_with_question(command), 
    ("open", "chat"): lambda command: mistral.call_mistral_with_question(command), 
}

