<div align="center">

# ▶ YT Downloader

**A clean, dark-themed desktop app to download YouTube videos and audio — locally, privately, fast.**

yt-dlp · CustomTkinter · FFmpeg · PyInstaller

<br>

🌐 [Türkçe README için tıklayın / Read in Turkish](README.TR.md)

</div>

---

## ✨ Features

- 🎬 **Video download** — MP4 with quality selection (Best / 1080p / 720p / 480p / 360p)
- 🎵 **Audio extraction** — MP3 at 192kbps
- 🖼️ **Video preview** — Thumbnail, title and duration fetched automatically
- 📋 **Download queue** — Add multiple links, downloads run one by one in order
- ⏹ **Cancel button** — Stop the active download instantly
- 📁 **Custom save folder** — Choose any directory
- 🔇 **No ads, no trackers** — 100% local, connects directly to YouTube servers

---

## 🖥️ Screenshots

| Main Interface | Download in Progress |
|---|---|
| ![UI](assets/screenshot1.png) | ![Progress](assets/screenshot2.png) |

---

## ⚡ Quick Start

### Requirements
- Python 3.8+
- FFmpeg (required for MP3 and high-quality video)

### Install dependencies

```bash
pip install yt-dlp customtkinter Pillow
```

### Run

```bash
python youtube_downloader.py
```

---

## 📦 Build Portable EXE

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Convert your icon (optional)

```bash
python -c "from PIL import Image; img = Image.open('icon.png').convert('RGBA'); img.save('icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
```

### 3. Build

```bash
python -m PyInstaller --onefile --windowed --name "YT-Downloader" --icon="icon.ico" youtube_downloader.py
```

The `.exe` will be in the `dist/` folder.

### 4. Portable package (share with friends)

```
📁 YTDownloader-Portable/
   ├── YT-Downloader.exe
   ├── ffmpeg.exe
   ├── ffplay.exe
   └── ffprobe.exe
```

> Zip these 4 files and share. No installation needed on the target PC.

---

## 🔧 FFmpeg Setup (Windows)

1. Download `ffmpeg-release-essentials.zip` from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Extract and place `ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe` into `C:\ffmpeg\bin\`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: `ffmpeg -version`

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Download engine | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| GUI framework | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Image handling | [Pillow](https://python-pillow.org/) |
| Video processing | [FFmpeg](https://ffmpeg.org/) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## ⚠️ Disclaimer

This tool is intended for **personal use only**.
Please respect YouTube's Terms of Service. Do not use for commercial redistribution.

---

## 📄 License

MIT License — free to use, modify and distribute.

<div align="center">
<br>
Made with ❤️ · Powered by yt-dlp
</div>
