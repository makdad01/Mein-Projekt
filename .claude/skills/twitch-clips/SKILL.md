---
name: twitch-clips
description: Sucht die Twitch-Clips der letzten 12 Stunden von Makis Lieblings-Streamern heraus und wählt die 3–5 mit dem größten Viral-Potenzial für TikTok aus (max. 59 Sekunden). Nutzen, wenn Maki nach Clips, Twitch-Highlights oder Clip-Vorschlägen fragt, beim geplanten 12-Stunden-Lauf, oder wenn Maki zurückmeldet, welche Clips viral gegangen sind.
---

# Twitch-Clips für TikTok auswählen

Ziel: Aus allen Clips der letzten **12 Stunden** die **3–5 besten** für Makis TikTok finden.
Du lieferst **Links + Begründung**, keine Videodateien.

## Streamer-Liste

Gepflegt in `tiktok/clips/streamer.md`. Nur diese Kanäle durchsuchen, außer Maki sagt etwas anderes.

## Harte Regeln

1. **Länge ≤ 59 Sekunden.** Längere Clips fliegen raus.
2. **Zeitraum:** nur Clips, die in den letzten 12 Stunden erstellt wurden.
3. **Sprache:** Deutsch bevorzugt (alle Streamer der Liste sind deutsch).
4. Keine Clips mit Gewalt, Hass, sexuellen Inhalten oder echten Privatdaten – die bringen Strikes auf TikTok.

## Ablauf

1. Clips abrufen: `python3 .claude/skills/twitch-clips/fetch_clips.py > <scratchpad>/clips.json`
   Gibt alle Clips ≤ 59 s der letzten 12 h als JSON aus, sortiert nach Views pro Stunde.
   Der Twitch-Zugangscode wird automatisch vom Proxy an api.twitch.tv angehängt.
   Bei **Fehler 401**: Code abgelaufen → Maki benachrichtigen, Anleitung in `tiktok/clips/README.md` („Code erneuern“).
2. Filtern: Dauer ≤ 59 s.
3. Jeden Clip mit dem **Viral-Score** bewerten (unten).
4. Top 3–5 auswählen – höchstens 2 vom selben Streamer, damit es abwechslungsreich bleibt.
5. Ergebnis als `tiktok/clips/JJJJ-MM-TT-HHMM.md` speichern, nach `main` committen und pushen.

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
- Twitch zählt Views verzögert. Sehr junge Clips (< 1 h) nicht nur nach Views pro Stunde bewerten.
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
