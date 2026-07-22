# Lyrics Bar GNOME Extension

A native GNOME Shell Extension that displays synchronized lyrics for the currently playing song in the top bar.

## Features
- Detects the current song playing in Firefox or Spotify via MPRIS.
- Fetches synchronized lyrics from open APIs (lrclib).
- Updates the top bar in real-time with the current line being sung.

## Installation

1. Copy the `lyrics-bar-extension` folder to your GNOME Shell extensions directory:
   ```bash
   cp -r lyrics-bar-extension ~/.local/share/gnome-shell/extensions/lyrics-bar@vaibhav.example.com
   ```
2. Log out and log back in, or restart GNOME Shell (Alt+F2, type `r`, Enter - on X11 only).
3. Enable the extension using the "Extensions" app or `gnome-extensions enable lyrics-bar@vaibhav.example.com`.
