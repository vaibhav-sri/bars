import dbus
import urllib.request
import urllib.parse
import json
import os
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
        properties_manager = dbus.Interface(
            player, 'org.freedesktop.DBus.Properties')
        metadata = properties_manager.Get(
            'org.mpris.MediaPlayer2.Player', 'Metadata')
        position = properties_manager.Get(
            'org.mpris.MediaPlayer2.Player', 'Position')
        status = properties_manager.Get(
            'org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
        return metadata, position, status
    except Exception:
        return None, None, None


def fetch_lyrics(artist, title):
    try:
        url = f"https://lrclib.net/api/get?artist_name={
            urllib.parse.quote(artist)}&track_name={
            urllib.parse.quote(title)}"
        req = urllib.request.Request(
            url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
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
                if cache.get('artist') == artist and cache.get(
                        'title') == title:
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


class LyricsDaemon:
    def __init__(self):
        self.last_output = None
        self.last_artist = None
        self.last_title = None
        self.parsed_lyrics = None
        self.fallback_text = None

    def tick(self):
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
                return "🎵 No player"

            metadata, position, status = get_metadata(firefox_player)
            if metadata is None:
                return "🎵 No metadata"

            artist_list = metadata.get('xesam:artist', [])
            artist = str(artist_list[0]) if artist_list else ''
            title = str(metadata.get('xesam:title', ''))

            if not artist or not title:
                return "🎵 Nothing playing"

            if artist != self.last_artist or title != self.last_title:
                lrc = get_cached_lyrics(artist, title)
                self.parsed_lyrics = parse_synced_lyrics(lrc) if lrc else None
                self.last_artist = artist
                self.last_title = title
                self.fallback_text = f"🎵 {title}"

            current_line = self.fallback_text

            if status in ["Playing", "Paused"]:
                pos_sec = int(position) / 1000000.0 if position else 0

                if self.parsed_lyrics:
                    found_line = False
                    for time_sec, text in reversed(self.parsed_lyrics):
                        if pos_sec >= time_sec:
                            if text:
                                current_line = text
                            found_line = True
                            break
                    if not found_line:
                        current_line = "🎵 ..."

            return current_line

        except Exception:
            return None


def main():
    daemon = LyricsDaemon()
    while True:
        current_line = daemon.tick()
        if current_line is not None and current_line != daemon.last_output:
            print(current_line, flush=True)
            daemon.last_output = current_line
        time.sleep(0.1)


if __name__ == '__main__':
    main()
