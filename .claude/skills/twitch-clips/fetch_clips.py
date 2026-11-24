#!/usr/bin/env python3
"""Holt die Twitch-Clips seit dem letzten geplanten Lauf für die Streamer aus
tiktok/clips/config.json, filtert auf <= 59 s, blendet schon empfohlene aus und gibt sie
als JSON aus, sortiert nach Views pro Stunde. Der Zugangscode wird vom Proxy an
api.twitch.tv angehängt.

Lauf-Zeiten (deutsche Zeit) stehen in config.json unter "laufzeiten". Ohne Argument wird
das Zeitfenster automatisch bestimmt: vom vorletzten bis zum letzten Lauf-Zeitpunkt
(minus 15 min Überlappung) bis jetzt. Beispiel um 08:03 -> Clips von 01:45 bis 08:03.

Aufruf:  python3 .claude/skills/twitch-clips/fetch_clips.py          (automatisch)
         python3 .claude/skills/twitch-clips/fetch_clips.py 3       (feste Stundenzahl)
"""
import json, sys, urllib.request, urllib.parse, urllib.error, datetime as dt, pathlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[3]
cfg = json.load(open(ROOT / "tiktok/clips/config.json"))
BERLIN = ZoneInfo("Europe/Berlin")
now = dt.datetime.now(dt.timezone.utc)
fmt = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def window_start():
    if len(sys.argv) > 1:
        return now - dt.timedelta(hours=float(sys.argv[1]))
    hours = sorted(cfg.get("laufzeiten", [0, 2, 8, 12, 18, 20, 22]))
    local = now.astimezone(BERLIN) + dt.timedelta(minutes=30)  # Lauf darf bis 30 min spät sein
    slots = []
    for day in (-1, 0):
        base = (local + dt.timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
        slots += [base.replace(hour=h) for h in hours]
    slots = [t for t in sorted(slots) if t <= local]
    prev_slot = slots[-2]  # der Lauf davor
    return prev_slot - dt.timedelta(minutes=15)

start = window_start()

def get(params):
    url = "https://api.twitch.tv/helix/clips?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Client-Id": cfg["twitch_client_id"],
        "Authorization": "Bearer proxy-injected",  # echter Code kommt vom Proxy
    })
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("FEHLER 401: Twitch-Zugangscode ungültig oder abgelaufen – siehe tiktok/clips/README.md, Abschnitt 'Code erneuern'.")
        raise

clips = []
for login, bid in cfg["streamer"].items():
    cursor = None
    while True:
        params = {"broadcaster_id": bid, "started_at": fmt(start), "ended_at": fmt(now), "first": 100}
        if cursor:
            params["after"] = cursor
        d = get(params)
        for c in d["data"]:
            if c["duration"] > 59:
                continue
            created = dt.datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
            age_h = max((now - created).total_seconds() / 3600, 0.25)
            clips.append({
                "streamer": c["broadcaster_name"],
                "titel": c["title"],
                "dauer_s": round(c["duration"], 1),
                "views": c["view_count"],
                "views_pro_stunde": round(c["view_count"] / age_h),
                "erstellt": c["created_at"],
                "alter_h": round(age_h, 1),
                "sprache": c["language"],
                "geclippt_von": c["creator_name"],
                "url": c["url"],
            })
        cursor = d.get("pagination", {}).get("cursor")
        if not cursor or not d["data"]:
            break

# Schon empfohlene Clips rausfiltern, damit jede Stunde neue Vorschläge kommen
seen_file = ROOT / "tiktok/clips/empfohlen.txt"
seen = set(seen_file.read_text().split()) if seen_file.exists() else set()
clips = [c for c in clips if c["url"] not in seen]

clips.sort(key=lambda c: c["views_pro_stunde"], reverse=True)
print(json.dumps({"zeitraum_berlin": [start.astimezone(BERLIN).strftime("%d.%m. %H:%M"), now.astimezone(BERLIN).strftime("%d.%m. %H:%M")], "zeitraum_utc": [fmt(start), fmt(now)], "anzahl": len(clips), "schon_empfohlen_ausgeblendet": len(seen), "clips": clips}, ensure_ascii=False, indent=1))
