# Yard

**Yet Another yt-dlp** - A simple, fast, and robust video downloader built with Flet.

![Yard Screenshot](docs/screenshot.png)

## Features

- 🎬 **Download videos** from YouTube and 1000+ websites
- 🎵 **Audio extraction** - MP3, M4A, WAV formats
- 📊 **Quality selection** - Best, 1080p, 720p, 480p
- 📦 **Multiple formats** - MP4, MKV, WEBM
- 📋 **Playlist support** - Download entire playlists
- 📂 **Download queue** - Add multiple URLs
- 💾 **Remember settings** - Preferences saved automatically
- 📋 **Auto-paste** - Detects URLs from clipboard on startup
- ⌨️ **Keyboard shortcuts** - Press Enter to download

## Installation

### Download Release

Download the latest `yard.exe` from [Releases](../../releases).

### Run from Source

**Requirements:** Python 3.9+

```bash
# Clone the repo
git clone https://github.com/razikdontcare/yard.git
cd yard

# Install dependencies
pip install flet yt-dlp imageio-ffmpeg pyperclip

# Run the app
flet run src/main.py
```

### Using uv

```bash
uv run flet run
```

### Using Poetry

```bash
poetry install
poetry run flet run
```

## Build Executable

```bash
flet pack src/main.py --name yard
```

The executable will be created in the `dist/` folder.

## Tech Stack

- **[Flet](https://flet.dev)** - UI Framework
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - Download engine
- **[FFmpeg](https://ffmpeg.org)** - Media processing (bundled via imageio-ffmpeg)

## License

MIT

## Author

**Razik** - [GitHub](https://github.com/razikdontcare)