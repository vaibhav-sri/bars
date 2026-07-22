import dbus
import urllib.request
import urllib.parse
import json
import os
import sys

CACHE_FILE = '/tmp/lyrics_cache.json'

def get_mpris_players():
    bus = dbus.SessionBus()
    players = []
    for service in bus.list_names():
        if service.startswith('org.mpris.MediaPlayer2.'):
            players.append(service)
    return players

def get_metadata(service):
    bus = dbus.SessionBus()
    try:
        player = bus.get_object(service, '/org/mpris/MediaPlayer2')
        properties_manager = dbus.Interface(player, 'org.freedesktop.DBus.Properties')
        metadata = properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        position = properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Position')
        status = properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
        return metadata, position, status
    except Exception:
        return None, None, None

def fetch_lyrics(artist, title):
    try:
        url = f"https://lrclib.net/api/get?artist_name={urllib.parse.quote(artist)}&track_name={urllib.parse.quote(title)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('syncedLyrics') or data.get('plainLyrics')
    except Exception:
        return None

def parse_synced_lyrics(lrc):
    lines = []
    if not lrc:
        return lines
    for line in lrc.split('\n'):
        if line.startswith('[') and ']' in line:
            time_str, text = line[1:].split(']', 1)
            try:
                m, s = time_str.split(':')
                seconds = int(m) * 60 + float(s)
                lines.append((seconds, text.strip()))
            except ValueError:
                continue
    return lines

def get_cached_lyrics(artist, title):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                if cache.get('artist') == artist and cache.get('title') == title:
                    return cache.get('lyrics')
        except Exception:
            pass
    
    lrc = fetch_lyrics(artist, title)
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({'artist': artist, 'title': title, 'lyrics': lrc}, f)
    except Exception:
        pass
    
    return lrc

def main():
    players = get_mpris_players()
    firefox_player = None
    for p in players:
        if 'firefox' in p or 'spotify' in p.lower():
            firefox_player = p
            break
            
    if not firefox_player and players:
        firefox_player = players[0]
        
    if not firefox_player:
        print("🎵 No player")
        return

    metadata, position, status = get_metadata(firefox_player)
    if not metadata:
        print("🎵 No metadata")
        return
        
    artist_list = metadata.get('xesam:artist', [])
    artist = str(artist_list[0]) if artist_list else ''
    title = str(metadata.get('xesam:title', ''))
    
    if not artist or not title:
        print("🎵 Nothing playing")
        return
        
    # position is in microseconds
    pos_sec = int(position) / 1000000.0 if position else 0

    lrc = get_cached_lyrics(artist, title)
    
    if not lrc:
        print(f"🎵 {artist} - {title}")
        return
        
    parsed = parse_synced_lyrics(lrc)
    if not parsed:
        print(f"🎵 {artist} - {title}")
        return
        
    current_line = "🎵 ..."
    for time_sec, text in parsed:
        if pos_sec >= time_sec:
            current_line = text if text else "🎵 ..."
        else:
            break
            
    if current_line.strip() == "":
        current_line = f"🎵 {title}"
        
    print(current_line)

if __name__ == '__main__':
    main()
