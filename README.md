<div align="center">
  <h1>Bars</h1>
  <p><b>A beautifully native GNOME Shell Extension that displays synchronized lyrics in your top bar.</b></p>
</div>

<br>

**Bars** is a lightweight, zero-latency GNOME extension that instantly syncs the lyrics of the currently playing song and renders them right in your top panel. It's built for efficiency, leveraging an event-driven daemon that guarantees instantaneous updates without bloating your system.

## Features

- **Zero Latency Engine**: Powered by a custom Python daemon using asynchronous I/O streams. The lyrics update the millisecond the song advances.
- **Universal Support**: Works seamlessly out of the box with Firefox, Spotify, Chrome, or any MPRIS-compatible media player.
- **Synchronized Perfection**: Fetches highly accurate, time-synced `.lrc` lyrics from the [lrclib.net](https://lrclib.net/) open API.
- **Native Aesthetic**: Carefully designed to look and feel like a first-class GNOME citizen, cleanly integrated into the top bar.

---

## Installation

### 1. Manual Install (Linux / Fedora 44+)

Clone or link the repository into your local GNOME Shell extensions directory:

```bash
# Clone the repository
git clone https://github.com/vaibhav-sri/bars.git ~/.local/share/gnome-shell/extensions/bars@vaibhav-sri.github.com

# Or, if you already have it downloaded:
ln -s /path/to/bars ~/.local/share/gnome-shell/extensions/bars@vaibhav-sri.github.com
```

### 2. Enable the Extension

Because GNOME Shell needs to read new extensions on startup, you must log out of your session and log back in. (If you are on X11, simply press `Alt+F2`, type `r`, and hit `Enter`).

Enable the extension using your terminal:
```bash
gnome-extensions enable bars@vaibhav-sri.github.com
```

---

## Architecture Deep-Dive

To prevent the overhead and lag of repeatedly running scripts (a common pitfall in other extensions), **Bars** employs a long-running background daemon (`bars.py`). 

The daemon continuously polls the MPRIS interface using a lightweight `100ms` loop and flushes lyric changes directly to `stdout`. The GNOME Shell frontend (`extension.js`) uses `Gio.Subprocess` to hook into this output stream via `Gio.DataInputStream`. This completely eliminates process spawning overhead and provides true real-time synchronization.

---

## Development & Testing

We maintain a strict, comprehensive test suite to ensure edge cases (e.g., malformed `.lrc` files, corrupted local caches, missing metadata, and API rate limits) are handled gracefully without ever crashing the shell.

### Setting up checks
Install the required testing and linting packages:
```bash
python3 -m pip install --user pytest flake8 autopep8
```

### Running Unit Tests
Execute the test suite to verify the core daemon logic:
```bash
python3 -m pytest test_bars.py
```

### Linting & Formatting
Ensure the codebase remains clean and adheres to PEP-8 standards:
```bash
# Check for linting errors
python3 -m flake8 bars.py test_bars.py

# Auto-format code
python3 -m autopep8 --in-place --aggressive --aggressive bars.py test_bars.py
```

---

<div align="center">
  Built for the GNOME Desktop.
</div>
