# Best-of-Videos „Top-5-Momente“

Pro Streamer ein Ranking-Video (5 Clips, Countdown, 61–100 s) im festen Maini-Design → **[DESIGN.md](DESIGN.md)**.

- `render.py` – baut das fertige Video aus einem Plan + 5 Clip-Dateien
- `JJJJ-MM/<kanal>.json` – Plan pro Streamer und Monat (Titel, Kurztitel mit Emoji, Twitch-Links)
- Clip-Dateien liegen in `JJJJ-MM/clips/<kanal>/5.mp4 … 1.mp4` (nicht im Git)

Voraussetzungen: ffmpeg, Python mit `Pillow`, `numpy`, `faster-whisper` (`pip install faster-whisper`).
