# Design „HIGHLIGHTS MOGDITV“ (fest, für ALLE Streamer gleich)

Festgelegt am 29.11.2026 nach Makis Designbriefing. Umgesetzt in `render.py`, Muster: [vorlage/vorlage-leer.png](vorlage/vorlage-leer.png) und [vorlage/vorlage-beispiel.png](vorlage/vorlage-beispiel.png).
Werte nicht pro Streamer ändern – der Kanal soll wiedererkennbar sein.

**Reihenfolge von oben nach unten:**
1. Überschrift „STREAMER HIGHLIGHTS“, darunter klein „MOGDITV“
2. großes, waagerechtes Videofenster
3. Video-Titel (z. B. „DIE BESTEN ABUGOKU & ABDI MOMENTE“)
4. Rangliste 1–5 untereinander
5. dezentes Wasserzeichen „@MOGDITV“ (mittig im Videofenster)

| Element | Festlegung |
|---|---|
| Format | 9:16, 1080×1920, 30 fps, 61–100 s, 5 Clips, Countdown Platz 5 → 1 |
| Hintergrund | derselbe Clip vergrößert, stark verschwommen, dunkel-violett eingefärbt (#14082A, 62 %) – ruhig, keine Deko |
| Überschrift oben | Rot (#E2202C), weißer Rand, schwarzer Schatten, leicht nach oben gebogen, Inter Display Black Italic |
| Kanalname | „MOGDITV“ klein, weiß, gesperrt, direkt unter der Überschrift |
| Videofenster | 1032×581 (16:9), ab y=290, dünner violetter Rahmen (#8B5CF6, 3 px), keine Neon-Effekte |
| Wasserzeichen | „@MOGDITV“ mittig im Videofenster, dunkles Violett (#4C1D95), sehr geringe Deckkraft |
| Titel | unter dem Video, zweizeilig, weiß, fett, kursiv, schwarzer Schatten, dünner violetter Rand + kurzer violetter Strich darunter. Kein Rot/Pink |
| Rangliste | 1.–5. untereinander, links, weiß, fett kursiv, schwarzer Schatten; „1.“ mit violettem Rand hervorgehoben; reicht bis ca. y=1800 |
| Kurztitel | erscheinen nach jedem Clip neben seiner Zahl (weiß, kursiv, mit Emoji) |
| Untertitel | Whisper, unten im Videofenster, weiß, ein Wort hellviolett (#C4B5FD) |
| Ende | letzte 3 s: „WELCHER WAR AM BESTEN? AB IN DIE KOMMENTARE“ |
| Themen | keine Videos mit dem Thema „schlägt Frauen“ und keine Clips mit echten Personen wie Julia (Freundin) in solchem Kontext – TikTok löscht so etwas, Strike-Gefahr |
| Verboten | „BLEIB DA LUCA!“, Autos, Palmen, Sonnenuntergänge, Skylines, Symbole, Gaming-Effekte, Zahlen nebeneinander |

Muster-Bild erzeugen: `python3 tiktok/best-of/render.py --vorlage "PSYCHO ZARBEX" muster.png [beispielbild.png]`

## Ablauf pro Streamer
1. Claude analysiert die Twitch-Clips des Monats (offizielle API) und wählt ein Thema + 5 Clips → `JJJJ-MM/<kanal>.json`
2. Claude lädt die 5 Clips selbst mit `yt-dlp` (von Maki am 29.11.2026 erlaubt), schaut sie an (Standbilder + Whisper-Text) und prüft auf doppelte Szenen
3. Claude schaut sich die Untertitel an, schneidet Leerlauf weg (`start`/`ende`) und rendert:
   `python3 tiktok/best-of/render.py tiktok/best-of/JJJJ-MM/<kanal>.json <kanal>.mp4`
4. Maki gibt Feedback → hier eintragen, dann nächster Streamer.

## Reihenfolge der Streamer
1. Zarbex (November 2026) – in Arbeit
2. weitere nach Makis Ansage

## Feedback zum Design
| Datum | Feedback | Änderung |
|---|---|---|
| 29.11.2026 | Psycho Zarbex gerendert (94,8 s) | Clips per yt-dlp geladen (Maki erlaubt). „Kurze Zündschnur“ = gleiche Szene wie „Prügelei“ → „Kurzer Ausraster“. Eigene Untertitel aus, weil Zarbex' Overlay schon Untertitel hat. Abschlussfrage oben im Videofenster |
| 29.11.2026 | Psycho Zarbex: alle 5 Clips abgenommen ✅ | warte auf Clip-Dateien |
| 29.11.2026 | Psycho Zarbex: Platz 5 „Zarbex der Psycho“ passt nicht | ersetzt durch „Schwerer Verkehrsunfall“ |
| 29.11.2026 | Psycho Zarbex: Maki will „Zarbi geht Crashout“ dazu | Instant Karma raus, Crashout auf Platz 4, Psycho auf 5 |
| 29.11.2026 | Psycho Zarbex: Platz 3 (Prügelei) + 1 (Schradin) gut; Rollator, „tritt mein Auto“, „Lucia umfahren“ raus | ersetzt durch Instant Karma, Zarbex der Psycho, Kurze Zündschnur |
| 29.11.2026 | Überschrift → „STREAMER HIGHLIGHTS“, darunter „MOGDITV“, Wasserzeichen → „@MOGDITV“ | angepasst |
| 29.11.2026 | Neues Designbriefing HIGHLIGHTS MOGDITV | komplettes Layout ersetzt (altes gelbes Design verworfen) |
| 28.11.2026 | Zarbex: Bigfoot + „Große Fresse“ raus, „Wir grüßen, wir sind nett“ rein, einen Clip darf Claude wählen | Plan angepasst (Claude wählte „Ach du Kacke“) |
