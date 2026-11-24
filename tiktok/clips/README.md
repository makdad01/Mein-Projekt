# Twitch-Clips

Alle 12 Stunden werden die besten 3–5 Twitch-Clips (≤ 59 s) der Lieblings-Streamer ausgewählt (Skill `twitch-clips`).

- [streamer.md](streamer.md) – welche Kanäle durchsucht werden
- [feedback.md](feedback.md) – Makis Rückmeldungen, was viral ging
- [learnings.md](learnings.md) – daraus abgeleitete Muster

## Zeitplan

Zwei Läufe pro Tag (deutsche Zeit), jeweils für die letzten 12 Stunden:

| Lauf | Deckt ab | Warum |
|---|---|---|
| **ca. 08:45** | Abend- und Nachtstreams (ca. 20:45–08:45) | Die meisten großen Streams laufen abends/nachts – morgens liegen die besten Clips bereit, Posten mittags/nachmittags |
| **ca. 20:45** | Tagesstreams (ca. 08:45–20:45) | Clips vom Nachmittag frisch zur Prime-Time am Abend posten |

## Einrichtung

- [x] Streamer-Liste bestätigen
- [x] Twitch-Entwickler-App anlegen (dev.twitch.tv/console) → Client-ID in [config.json](config.json)
- [x] Zugangscode sicher in der Umgebung hinterlegt (gilt für api.twitch.tv)
- [x] Automatischer Lauf täglich um 08:43 und 20:43 (geplante Aufgabe „Twitch-Clips für TikTok“, mit Push-Benachrichtigung)

## Code erneuern (wenn Fehler 401 kommt)

Der Twitch-Zugangscode läuft irgendwann ab. Dann:
1. Diesen Link öffnen und bei Twitch auf „Autorisieren“ tippen:
   https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=ufy4jblnij38nzh9igcg8zt9lrfyx0&redirect_uri=https://localhost&scope=
2. Auf der Fehlerseite in die **Adresszeile** schauen: `https://localhost/#access_token=XXXX&scope=…`
3. Claude sagen, dass ein neuer Code da ist → Claude öffnet das sichere Formular → nur `XXXX` eintragen.
