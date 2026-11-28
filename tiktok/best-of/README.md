# Best-of-Videos (Monats-Rankings)

Pro Streamer ein Video „<STREAMER> – Best of <Monat>“: die 5 besten Clips als Countdown (Platz 5 → 1), immer im gleichen Maini-Design, 1080×1920, mind. 1:01 lang.

## Design (für alle Videos gleich)
- Oben: Streamer-Name groß in Weiß, darunter gelbes Banner „BEST OF NOVEMBER 2026“
- Mitte: Clip mit gelbem Rahmen, Hintergrund = derselbe Clip unscharf
- „#5“ … „#1“ blinkt am Anfang jedes Clips oben links
- Unten: Rangliste 1–5, wird von 5 nach 1 aufgedeckt, aktueller Platz rot markiert
- Am Ende: „WELCHER WAR DER BESTE? AB IN DIE KOMMENTARE“ (Kommentare = Reichweite)
- Lautstärke wird automatisch angeglichen

## So entsteht ein Video
1. Claude sucht die Top-5-Clips pro Streamer raus → `JJJJ-MM/<kanal>.json` + Übersicht `JJJJ-MM/README.md`
2. **Maki lädt die Clips runter** (Links stehen in der Übersicht) und speichert sie als
   `JJJJ-MM/clips/<kanal>/5.mp4` … `1.mp4` – oder schickt sie Claude einfach in den Chat.
   (Claude darf die Videodateien nicht selbst von Twitch laden – nur die Clip-Infos über die offizielle API.)
3. Claude rendert: `python3 tiktok/best-of/render.py tiktok/best-of/2026-11/trymacs.json trymacs.mp4`
4. Optional pro Clip `start`/`ende` (Sekunden) setzen, um Leerlauf rauszuschneiden; `label` = Text in der Rangliste; `handle` = dein TikTok-Name.
