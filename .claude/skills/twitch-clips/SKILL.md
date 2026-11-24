---
name: twitch-clips
description: Sucht jede Stunde die neuen Twitch-Clips der letzten 60 Minuten von Makis Lieblings-Streamern heraus und wählt die 5 noch nicht empfohlenen mit dem größten Viral-Potenzial für TikTok aus (max. 59 Sekunden). Nutzen, wenn Maki nach Clips, Twitch-Highlights oder Clip-Vorschlägen fragt, beim stündlichen Lauf, oder wenn Maki zurückmeldet, welche Clips viral gegangen sind.
---

# Twitch-Clips für TikTok auswählen

Ziel: **Jede Stunde** aus allen Clips der **letzten 60 Minuten** die **Top 5** für Makis TikTok finden – nur Clips, die noch nie empfohlen wurden.
Du lieferst **Links + Begründung**, keine Videodateien. Maki schaut sie an und lädt hoch, was ihm gefällt.

## Streamer-Liste

Gepflegt in `tiktok/clips/streamer.md`. Nur diese Kanäle durchsuchen, außer Maki sagt etwas anderes.

## Harte Regeln

1. **Länge ≤ 59 Sekunden.** Längere Clips fliegen raus.
2. **Zeitraum:** nur Clips der letzten 60 Minuten (das Skript schaut 75 min zurück, damit bei leicht verspätetem Lauf nichts durchrutscht – doppelte fallen durch `empfohlen.txt` raus). So bekommt Maki jeden Clip mit Viral-Potenzial genau einmal.
3. **Keine Wiederholungen:** Clips aus `tiktok/clips/empfohlen.txt` nie nochmal vorschlagen (das Skript filtert sie raus).
4. **Sprache:** Deutsch bevorzugt (alle Streamer der Liste sind deutsch).
5. Keine Clips mit Gewalt, Hass, sexuellen Inhalten oder echten Privatdaten – die bringen Strikes auf TikTok.

## Ablauf

1. Clips abrufen: `python3 .claude/skills/twitch-clips/fetch_clips.py > <scratchpad>/clips.json`
   Gibt alle Clips ≤ 59 s der letzten 75 min als JSON aus, sortiert nach Views pro Stunde.
   Der Twitch-Zugangscode wird automatisch vom Proxy an api.twitch.tv angehängt.
   Bei **Fehler 401**: Code abgelaufen → Maki benachrichtigen, Anleitung in `tiktok/clips/README.md` („Code erneuern“).
2. Filtern: Dauer ≤ 59 s.
3. Jeden Clip mit dem **Viral-Score** bewerten (unten).
4. **Top 5** auswählen – höchstens 2 vom selben Streamer, damit es abwechslungsreich bleibt. Gibt es weniger als 5 brauchbare neue Clips, nur die brauchbaren nehmen und das dazuschreiben.
5. Die URLs der ausgewählten Clips ans Ende von `tiktok/clips/empfohlen.txt` anhängen (eine pro Zeile).
6. Ergebnis als `tiktok/clips/JJJJ-MM-TT-HHMM.md` speichern, nach `main` committen und pushen.

## Viral-Score (0–100)

| Kriterium | Gewicht | Wie messen |
|---|---|---|
| **Views pro Stunde** seit Erstellung | 35 | im Vergleich zu den anderen Clips des Laufs (Rang → Punkte) |
| **Hook in den ersten 3 Sekunden** | 20 | Titel/Inhalt deutet auf sofortige Reaktion hin (Schrei, Rage, Lachflash, Fail, „Ich bin raus“) |
| **Verständlich ohne Kontext** | 15 | Witz funktioniert auch für Leute, die den Stream nicht kennen |
| **Länge** | 10 | 15–40 s ideal, 41–59 s okay, < 10 s schwach |
| **Streamer-Bonus** | 10 | aus `tiktok/clips/learnings.md` – Streamer, deren Clips bei Maki viral gingen |
| **Learnings-Bonus** | 10 | passt zu Mustern, die laut `learnings.md` funktionieren |

Lies **vor jedem Lauf** `tiktok/clips/learnings.md` und wende die Learnings an.

## Grenzen (ehrlich angeben)
- Du kannst die Clips **nicht anschauen**, nur Titel, Länge und Zahlen sehen. Hook und Kontext sind aus dem Titel geschätzt – das im Ergebnis dazuschreiben.
- Twitch zählt Views verzögert, und alle Clips sind höchstens ~1 h alt. Deshalb zählen **Titel, Streamer und wie viele Leute denselben Moment geclippt haben** (mehrere Clips zur gleichen Zeit beim gleichen Streamer = großer Moment) genauso viel wie die Views.
- Clips mit dem Stream-Titel als Clip-Titel (z. B. „[DROPS] …“) sind meist unbenannt und schwer einzuschätzen → nur nehmen, wenn die Zahlen klar herausstechen.

## Ausgabeformat

```markdown
# Clips – <Datum, Uhrzeit>

| # | Streamer | Titel | Länge | Views | Score | Link |
|---|---|---|---|---|---|---|
| 1 | … | … | 0:23 | 12.400 | 87 | https://clips.twitch.tv/… |

### 1. <Titel>
- **Warum viral:** <1–2 Sätze>
- **Hook für TikTok:** <Texteinblendung für die ersten 2 Sekunden>
- **Caption:** <Vorschlag>
- **Hashtags:** <4–6>
```

## Lernen aus Makis Feedback

Wenn Maki meldet, welche Clips viral gingen (oder floppten):
1. In `tiktok/clips/feedback.md` eintragen: Datum, Clip, Streamer, Views/Likes auf TikTok, viral ja/nein.
2. Muster ableiten (Streamer, Art des Moments, Länge, Hook, Uhrzeit des Postings) und in `tiktok/clips/learnings.md` festhalten.
3. Wenn ein Muster mehrfach bestätigt ist: Gewichte im Viral-Score oben anpassen und die Änderung in `learnings.md` mit Datum notieren.
4. Committen und nach `main` pushen.
