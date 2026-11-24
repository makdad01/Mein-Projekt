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

## Einrichtung (Stand: noch nicht fertig)

- [ ] Streamer-Liste bestätigen
- [x] Twitch-Entwickler-App anlegen (dev.twitch.tv/console) → Client-ID in [config.json](config.json)
- [ ] Netzwerkzugriff auf `api.twitch.tv` und `id.twitch.tv` freigeben
- [ ] Zugangsschlüssel sicher hinterlegen
- [ ] Automatischen Lauf um ca. 08:45 und 20:45 einrichten
