# Lyrics Bar GNOME Extension

A native GNOME Shell Extension that displays synchronized lyrics for the currently playing song right in your top bar.

## Features
- **Zero Latency**: Uses a custom Python daemon and GNOME's asynchronous I/O streams for instant lyric updates.
- **Universal MPRIS Support**: Automatically detects playback from Firefox, Spotify, or any MPRIS-compatible player.
- **Synchronized Lyrics**: Fetches highly accurate synced `.lrc` lyrics from [lrclib.net](https://lrclib.net/).
- **Native Look**: Renders cleanly on the left side of the top bar with default GNOME styling.

## Architecture
To prevent the overhead and lag of repeatedly running scripts, this extension runs `lyrics.py` as a background daemon. The daemon continuously polls MPRIS using a lightweight `100ms` loop and flushes updates directly to `stdout`. 

The GNOME Shell Extension (`extension.js`) uses `Gio.Subprocess` to spawn the daemon exactly once upon initialization, hooking into its output stream via `Gio.DataInputStream`. This event-driven design guarantees ultra-low latency and minimal CPU footprint.

## Installation

1. Copy or link the `lyrics-bar-extension` folder to your GNOME Shell extensions directory:
   ```bash
   ln -s /path/to/lyrics-bar-extension ~/.local/share/gnome-shell/extensions/lyrics-bar@vaibhav.example.com
   ```
2. Log out and log back in, or restart GNOME Shell (Press `Alt+F2`, type `r`, then `Enter` - on X11 only).
3. Enable the extension using the "Extensions" app or via terminal:
   ```bash
   gnome-extensions enable lyrics-bar@vaibhav.example.com
   ```

## Development & Testing (Linux / Fedora 44)

We've set up a solid test suite to ensure edge cases (e.g., malformed lyrics, corrupted cache, missing metadata) are handled gracefully.

### Setting up checks
Install the required testing and linting tools:
```bash
python3 -m pip install --user pytest flake8 autopep8
```

### Running Unit Tests
Execute the comprehensive test suite to verify the daemon logic:
```bash
python3 -m pytest test_lyrics.py
```

### Linting & Formatting
Ensure the codebase remains clean and adheres to PEP-8 standards:
```bash
# Check for linting errors
python3 -m flake8 lyrics.py test_lyrics.py

# Auto-format code
python3 -m autopep8 --in-place --aggressive --aggressive lyrics.py test_lyrics.py
```
