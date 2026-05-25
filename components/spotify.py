import os
import requests
import random
from dotenv import load_dotenv
load_dotenv()


    
# SPOTIFY WEB API
CLIENT_ID = os.getenv("SPOTIFY_API_KEY")  
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")  

QUEUED_TRACKS = []

try:
    from .spotify_oauth import get_valid_access_token
except ImportError:
    from spotify_oauth import get_valid_access_token
OAUTH_AVAILABLE = True

def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Missing Spotify credentials. Add SPOTIFY_CLIENT_SECRET to .env file.")
        return None
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Failed to get access token: {response.status_code}")
        return None

def get_headers(user_specific=False):
    if user_specific and OAUTH_AVAILABLE:
        try:
            token = get_valid_access_token()
            if token:
                return {"Authorization": f"Bearer {token}"}
        except Exception as e:
            print(f"Failed to get user access token: {e}")
            print("Falling back to client credentials...")
    
    token = get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return None

def find_artist(artist_name):
    headers = get_headers()
    if not headers:
        print("Failed to get Spotify access token")
        return None
        
    url = "https://api.spotify.com/v1/search"
    params = {
        "q": artist_name,
        "type": "artist"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"Searching for artist: {artist_name}")
        artists = data.get("artists", {}).get("items", [])
        if artists:
            return artists[0]  # Return the first artist found
    return None

def play_artist(artist_name):
    headers = get_headers(user_specific=True)
    
    if not headers:
        print("Failed to get Spotify access token")
        return
    
    if artist_name == "":
        print("No artist name provided")
        return
        
    artist = find_artist(artist_name)
    
    if artist:
        url = f"https://api.spotify.com/v1/artists/{artist['id']}/top-tracks?market=US"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tracks = response.json().get("tracks", [])
            queue_tracks(tracks)
    else:
        print(f"Artist '{artist_name}' not found")
        
def play_artist_song(artist_name, song_name):
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get Spotify access token")
        return
    artist = find_artist(artist_name)
    if artist:
        url = f"https://api.spotify.com/v1/search"
        data = {
            "q": f"track:{song_name} artist:{artist_name}",
            "type": "track"
        }
        print(f"Searching for song: {song_name} by {artist_name}")
        response = requests.get(url, headers=headers, params=data)
        if response.status_code == 200:
            tracks = response.json().get("tracks", {}).get("items", [])
            if tracks:
                track_uri = tracks[0]['uri']
                play_url = "https://api.spotify.com/v1/me/player/queue"
                params = {
                    "uri": track_uri
                }
                play_response = requests.post(play_url, headers=headers, params=params)
                if play_response.status_code == 200:
                    print(f"Playing '{song_name}' by {artist_name}")
                elif play_response.status_code == 404:
                    print("No active Spotify device found. Please start Spotify and begin playing something first.")
                    play_pause_api()
                    play_artist_song(artist_name, song_name)
                elif play_response.status_code == 401:
                    print("Authorization failed. You may need to re-authorize the app.")
                else:
                    print(f"Failed to start playback: {play_response.status_code}")
            else:
                print(f"No tracks found for '{song_name}' by {artist_name}")
        else:
            print(f"Error searching for track: {response.status_code}")

def queue_tracks(tracks):
    global QUEUED_TRACKS
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get Spotify access token")
        return

    for track in random.sample(tracks, min(5, len(tracks))):
        track_uri = track['uri']
        queue_url = "https://api.spotify.com/v1/me/player/queue"
        params = {
            "uri": track_uri
        }
        queue_response = requests.post(queue_url, headers=headers, params=params)
        if queue_response.status_code == 200:
            print(f"Queued '{track['name']}'")
            QUEUED_TRACKS.append(track)
        else:
            print(f"{queue_response.status_code}")

def clear_queue():
    global QUEUED_TRACKS
    
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get Spotify access token")
        return
    
    queue = get_queue()

    for item in queue.get("queue", []):
        if item["name"] in [t['name'] for t in QUEUED_TRACKS]:
            skip_current_track()
            
    QUEUED_TRACKS.clear()
    skip_current_track()
    return

def get_queue():
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get Spotify access token")
        return
    queue_url = "https://api.spotify.com/v1/me/player/queue"
    response = requests.get(queue_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def skip_current_track():
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get Spotify access token")
        return

    skip_url = "https://api.spotify.com/v1/me/player/next"
    response = requests.post(skip_url, headers=headers)
    if response.status_code == 200:
        return 0
    else:
        print(f"Failed to skip track: {response.status_code}")

def test_queue():
    json = get_queue()
    print(json["queue"])
    print(len(json["queue"]))

def play_pause_api():
    headers = get_headers(user_specific=True)
    if not headers:
        print("Failed to get user access token")
        return

    play_url = "https://api.spotify.com/v1/me/player/play"
    response = requests.put(play_url, headers=headers)
    if response.status_code == 204:
        print("Playback paused")
    else:
        print(f"Failed to pause playback: {response.status_code}")

def user_profile():
    headers = get_headers(user_specific=True)
    if not headers:
        print("No user authorization. Falling back to media key...")
        return
    user_info = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if user_info.status_code == 200:
        print(user_info.json())
        return user_info.json()
    return None


if __name__ == "__main__":
    play_artist("Kendrick")
    clear_queue()