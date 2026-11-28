# Maini-Design „Top-5-Momente“ (fest, für ALLE Streamer gleich)

Festgelegt am 28.11.2026 nach Makis Vorgabe (Vorbilder: @by.alexz, @nickstrsp, @core.streamer0).
Umgesetzt in `render.py` – Werte dort nicht pro Streamer ändern, sonst sieht der Account uneinheitlich aus.

| Element | Festlegung |
|---|---|
| Format | 9:16, 1080×1920, 30 fps, H.264 hohe Qualität |
| Länge | **61–100 Sekunden**, genau 5 Clips, Countdown Platz 5 → 1 |
| Thema | alle 5 Clips mit gemeinsamem Thema (z. B. nur GTA 6 oder nur Ausraster) |
| Titel | oben, **gelb (#FFD21F)**, Inter Display Black, schwarze Kontur, max. 2 Zeilen. Muster: „<Streamer>' <krasseste/Psycho-/lustigste> Momente in <Thema> – Part <n>“ |
| Liste | darunter 1.–5., weiß mit Kontur. **Nach jedem Clip** (1,2 s vor seinem Ende) erscheint sein Kurztitel mit Emoji, z. B. „Granate apportieren 💣“ |
| Clip | mittig unter der Liste, volle Breite, leicht gezoomt; Hintergrund = derselbe Clip verschwommen + abgedunkelt (keine schwarzen Balken) |
| Untertitel | automatisch (Whisper), eingebrannt, GROSSBUCHSTABEN, weiß mit schwarzer Kontur, 1–3 Wörter, ein wichtiges Wort **gelb**, kleiner Pop-Effekt; im unteren Teil des Clips |
| Ende | letzte 3 s: „WELCHER WAR AM **KRANKSTEN**? AB IN DIE KOMMENTARE“ (bringt Kommentare → Reichweite) |
| Ton | Lautstärke aller Clips angeglichen (-14 LUFS) |

## Ablauf pro Streamer
1. Claude analysiert die Twitch-Clips des Monats (offizielle API) und wählt ein Thema + 5 Clips → `JJJJ-MM/<kanal>.json`
2. Maki lädt die 5 Clips über die Links runter und schickt sie Claude (Claude darf die Videodateien nicht selbst von Twitch laden)
3. Claude schaut sich die Untertitel an, schneidet Leerlauf weg (`start`/`ende`) und rendert:
   `python3 tiktok/best-of/render.py tiktok/best-of/JJJJ-MM/<kanal>.json <kanal>.mp4`
4. Maki gibt Feedback → hier eintragen, dann nächster Streamer.

## Reihenfolge der Streamer
1. Zarbex (November 2026) – in Arbeit
2. weitere nach Makis Ansage

## Feedback zum Design
| Datum | Feedback | Änderung |
|---|---|---|
