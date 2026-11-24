# Twitch-Clips

7× am Tag werden die 5 besten neuen Twitch-Clips (≤ 59 s) der Lieblings-Streamer ausgewählt (Skill `twitch-clips`).

- [streamer.md](streamer.md) – welche Kanäle durchsucht werden
- [feedback.md](feedback.md) – Makis Rückmeldungen, was viral ging
- [learnings.md](learnings.md) – daraus abgeleitete Muster

## Zeitplan

Zu festen Zeiten (deutsche Zeit) werden alle Clips **seit dem letzten Lauf** durchsucht und die **Top 5 neuen** empfohlen (Push-Benachrichtigung). Schon empfohlene Clips stehen in [empfohlen.txt](empfohlen.txt) und kommen nicht nochmal.

| Lauf | Zeitfenster |
|---|---|
| 00:00 | 22–24 Uhr |
| 02:00 | 0–2 Uhr |
| 08:00 | 2–8 Uhr |
| 12:00 | 8–12 Uhr |
| 18:00 | 12–18 Uhr |
| 20:00 | 18–20 Uhr |
| 22:00 | 20–22 Uhr |

Die Läufe starten jeweils ca. 3 Minuten nach der vollen Stunde, damit die Clips bis zur vollen Stunde schon da sind.

## Einrichtung

- [x] Streamer-Liste bestätigen
- [x] Twitch-Entwickler-App anlegen (dev.twitch.tv/console) → Client-ID in [config.json](config.json)
- [x] Zugangscode sicher in der Umgebung hinterlegt (gilt für api.twitch.tv)
- [x] Automatischer Lauf um 0, 2, 8, 12, 18, 20 und 22 Uhr (geplante Aufgabe „Twitch-Clips für TikTok“, mit Push-Benachrichtigung)

## Code erneuern (wenn Fehler 401 kommt)

Der Twitch-Zugangscode läuft irgendwann ab. Dann:
1. Diesen Link öffnen und bei Twitch auf „Autorisieren“ tippen:
   https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=ufy4jblnij38nzh9igcg8zt9lrfyx0&redirect_uri=https://localhost&scope=
2. Auf der Fehlerseite in die **Adresszeile** schauen: `https://localhost/#access_token=XXXX&scope=…`
3. Claude sagen, dass ein neuer Code da ist → Claude öffnet das sichere Formular → nur `XXXX` eintragen.
