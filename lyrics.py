import dbus
import urllib.request
import urllib.parse
import json
import os
import sys
import time

CACHE_FILE = '/tmp/lyrics_cache.json'

def get_mpris_players():
    try:
        bus = dbus.SessionBus()
        players = []
        for service in bus.list_names():
            if service.startswith('org.mpris.MediaPlayer2.'):
                players.append(service)
        return players
    except Exception:
        return []

def get_metadata(service):
    try:
        bus = dbus.SessionBus()
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
    last_output = None
    last_artist = None
    last_title = None
    parsed_lyrics = None
    fallback_text = None

    while True:
        try:
            players = get_mpris_players()
            firefox_player = None
            for p in players:
                if 'firefox' in p or 'spotify' in p.lower():
                    firefox_player = p
                    break
                    
            if not firefox_player and players:
                firefox_player = players[0]
                
            if not firefox_player:
                current_line = "🎵 No player"
                if current_line != last_output:
                    print(current_line, flush=True)
                    last_output = current_line
                time.sleep(1)
                continue

            metadata, position, status = get_metadata(firefox_player)
            if not metadata:
                current_line = "🎵 No metadata"
                if current_line != last_output:
                    print(current_line, flush=True)
                    last_output = current_line
                time.sleep(1)
                continue
                
            artist_list = metadata.get('xesam:artist', [])
            artist = str(artist_list[0]) if artist_list else ''
            title = str(metadata.get('xesam:title', ''))
            
            if not artist or not title:
                current_line = "🎵 Nothing playing"
                if current_line != last_output:
                    print(current_line, flush=True)
                    last_output = current_line
                time.sleep(1)
                continue

            # Update cache if song changed
            if artist != last_artist or title != last_title:
                lrc = get_cached_lyrics(artist, title)
                parsed_lyrics = parse_synced_lyrics(lrc) if lrc else None
                last_artist = artist
                last_title = title
                fallback_text = f"🎵 {title}"

            current_line = fallback_text
            
            if status == "Playing" or status == "Paused":
                pos_sec = int(position) / 1000000.0 if position else 0
                
                if parsed_lyrics:
                    # Sync offset tuning if needed, usually 0
                    pos_sec += 0.0 
                    
                    found_line = False
                    # We iterate backwards to find the most recent line that has passed
                    for time_sec, text in reversed(parsed_lyrics):
                        if pos_sec >= time_sec:
                            if text:
                                current_line = text
                            found_line = True
                            break
                    if not found_line:
                        current_line = "🎵 ..."

            if current_line != last_output:
                print(current_line, flush=True)
                last_output = current_line
                
        except Exception as e:
            pass
            
        # 100ms polling for very low latency lyrics sync!
        time.sleep(0.1)

if __name__ == '__main__':
    main()
