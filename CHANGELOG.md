# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-26
### Added
- Initial release of Bars: a lightweight, non-intrusive GNOME Shell extension for displaying live synced lyrics directly on the top bar.
- **Media Player Support**: Out-of-the-box support for MPRIS-compatible players including standalone Spotify, VLC, and web-based players like Spotify in Firefox.
- **Smart Metadata Parsing**: Advanced MPRIS parsing logic that intelligently handles metadata edge cases (e.g., Firefox presenting artists as strings instead of arrays).
- **Synced Lyrics Fetching**: Automatic real-time lyric fetching powered by the open-source LRCLIB API.
- **Local Caching**: Intelligent local caching (`/tmp/bars_cache.json`) that strictly stores only successful downloads, dramatically improving speed on replays and reducing network calls.
- **Native Integration**: Smart idle positioning logic that guarantees the Bars widget stays cleanly anchored to the far right of the GNOME top bar's left panel, preventing layout shuffling during session changes.
- **Privacy First**: Seamless lock-screen support that automatically hides active lyrics and reverts to a minimal song title display for privacy.
- **Testing Infrastructure**: Comprehensive automated test suite (`pytest`) covering the Python daemon's DBUS interactions, metadata extraction, and JSON data structures.
- **Community Ready**: Fully GPLv2+ compliant codebase featuring a comprehensive `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and robust `.gitignore`.
