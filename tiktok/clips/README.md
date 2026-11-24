# Twitch-Clips

Jede Stunde werden die 5 besten neuen Twitch-Clips (≤ 59 s) der Lieblings-Streamer ausgewählt (Skill `twitch-clips`).

- [streamer.md](streamer.md) – welche Kanäle durchsucht werden
- [feedback.md](feedback.md) – Makis Rückmeldungen, was viral ging
- [learnings.md](learnings.md) – daraus abgeleitete Muster

## Zeitplan

**Jede Stunde** werden die Clips der **letzten 60 Minuten** durchsucht und die **Top 5 neuen** Clips empfohlen (Push-Benachrichtigung). Schon empfohlene Clips stehen in [empfohlen.txt](empfohlen.txt) und kommen nicht nochmal.

## Einrichtung

- [x] Streamer-Liste bestätigen
- [x] Twitch-Entwickler-App anlegen (dev.twitch.tv/console) → Client-ID in [config.json](config.json)
- [x] Zugangscode sicher in der Umgebung hinterlegt (gilt für api.twitch.tv)
- [x] Automatischer Lauf jede Stunde (geplante Aufgabe „Twitch-Clips für TikTok“, mit Push-Benachrichtigung)

## Code erneuern (wenn Fehler 401 kommt)

Der Twitch-Zugangscode läuft irgendwann ab. Dann:
1. Diesen Link öffnen und bei Twitch auf „Autorisieren“ tippen:
   https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=ufy4jblnij38nzh9igcg8zt9lrfyx0&redirect_uri=https://localhost&scope=
2. Auf der Fehlerseite in die **Adresszeile** schauen: `https://localhost/#access_token=XXXX&scope=…`
3. Claude sagen, dass ein neuer Code da ist → Claude öffnet das sichere Formular → nur `XXXX` eintragen.
