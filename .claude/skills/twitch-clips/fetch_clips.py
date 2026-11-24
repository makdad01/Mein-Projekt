#!/usr/bin/env python3
"""Holt alle Twitch-Clips der letzten N Stunden (Standard 12) für die Streamer aus
tiktok/clips/config.json, filtert auf <= 59 s und gibt sie als JSON aus, sortiert nach
Views pro Stunde. Der Zugangscode wird vom Proxy an api.twitch.tv angehängt.

Aufruf:  python3 .claude/skills/twitch-clips/fetch_clips.py [stunden]
"""
import json, sys, urllib.request, urllib.parse, datetime as dt, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
cfg = json.load(open(ROOT / "tiktok/clips/config.json"))
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 12
now = dt.datetime.now(dt.timezone.utc)
start = now - dt.timedelta(hours=hours)
fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")

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
print(json.dumps({"zeitraum_utc": [fmt(start), fmt(now)], "anzahl": len(clips), "schon_empfohlen_ausgeblendet": len(seen), "clips": clips}, ensure_ascii=False, indent=1))
