#!/usr/bin/env python3
"""Baut aus 5 Clips ein fertiges TikTok-Video im Maini-Best-of-Design (1080x1920, 30 fps).

Aufruf:  python3 tiktok/best-of/render.py <plan.json> <ausgabe.mp4>

plan.json (Beispiel in vorlage-plan.json):
{
  "streamer": "TRYMACS",
  "untertitel": "BEST OF NOVEMBER 2026",
  "handle": "@deinname",
  "clips": [                      # Reihenfolge = Platz 5, 4, 3, 2, 1
    {"datei": "clips/5.mp4", "label": "Digger was", "start": 0, "ende": null},
    ...
  ]
}
"""
import json, os, subprocess, sys, tempfile

W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT2 = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
AKZENT = "0xFFD21F"      # Gelb – Makis Markenfarbe für alle Videos
ROT = "0xFF2D55"
VID_Y, VID_H = 430, 730  # Clip-Fenster (1080 breit, leicht gezoomt)
LIST_Y, ROW = 1230, 92


def dauer(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out)


def txt(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def segment(plan, idx, clip, tmp, out, letzter):
    rang = 5 - idx                       # idx 0 = Platz 5
    start = clip.get("start") or 0
    ende = clip.get("ende") or dauer(clip["datei"])
    d = ende - start
    labels = [c["label"] for c in plan["clips"]]   # labels[0] = Platz 5

    f = []
    f.append("[0:v]fps=30,setsar=1,split[a][b]")
    f.append(f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
             f"boxblur=40:6,eq=brightness=-0.32:saturation=1.2[bg]")
    f.append(f"[b]crop='min(iw,ih*{W}/{VID_H})':'min(ih,iw*{VID_H}/{W})',scale={W}:{VID_H}[fg]")
    f.append(f"[bg][fg]overlay=0:{VID_Y}[v0]")
    dt = []
    # Rahmen ums Clip-Fenster
    dt.append(f"drawbox=x=0:y={VID_Y-8}:w={W}:h=8:color={AKZENT}:t=fill")
    dt.append(f"drawbox=x=0:y={VID_Y+VID_H}:w={W}:h=8:color={AKZENT}:t=fill")
    # Kopf: Streamer-Name + Untertitel-Banner
    name = txt(tmp, "name.txt", plan["streamer"].upper())
    unter = txt(tmp, "unter.txt", plan["untertitel"].upper())
    dt.append(f"drawtext=fontfile={FONT}:textfile={name}:fontsize=128:fontcolor=white:"
              f"borderw=7:bordercolor=black:shadowx=0:shadowy=8:shadowcolor=black@0.6:x=(w-tw)/2:y=150")
    dt.append(f"drawtext=fontfile={FONT}:textfile={unter}:fontsize=54:fontcolor=black:"
              f"box=1:boxcolor={AKZENT}:boxborderw=18:x=(w-tw)/2:y=318")
    # Platz-Badge oben links im Clip (1,8 s eingeblendet)
    badge = txt(tmp, f"badge{idx}.txt", f"#{rang}")
    dt.append(f"drawtext=fontfile={FONT}:textfile={badge}:fontsize=150:fontcolor={AKZENT}:"
              f"borderw=8:bordercolor=black:x=40:y={VID_Y+30}:"
              f"alpha='if(lt(t,1.5),1,max(0,1-(t-1.5)/0.3))':enable='lt(t,1.8)'")
    # Rangliste 1–5: aufgedeckt sind Platz 5 .. aktueller Platz
    for r in range(1, 6):
        y = LIST_Y + (r - 1) * ROW
        aktiv = (r == rang)
        num = txt(tmp, f"n{idx}_{r}.txt", f"{r}.")
        dt.append(f"drawtext=fontfile={FONT}:textfile={num}:fontsize=66:"
                  f"fontcolor={AKZENT if r <= 3 else 'white'}:borderw=5:bordercolor=black:x=70:y={y}")
        if r >= rang:
            lab = labels[5 - r]
            lp = txt(tmp, f"l{idx}_{r}.txt", lab.upper())
            farbe = AKZENT if aktiv else "white"
            extra = f":box=1:boxcolor={ROT}@0.85:boxborderw=12" if aktiv else ""
            dt.append(f"drawtext=fontfile={FONT2}:textfile={lp}:fontsize=58:fontcolor={farbe}:"
                      f"borderw=5:bordercolor=black:x=175:y={y+6}{extra}")
    if plan.get("handle"):
        hp = txt(tmp, "handle.txt", plan["handle"])
        dt.append(f"drawtext=fontfile={FONT2}:textfile={hp}:fontsize=36:fontcolor=white@0.75:"
                  f"borderw=3:bordercolor=black:x=(w-tw)/2:y=1840")
    if letzter:
        cta = txt(tmp, "cta.txt", "WELCHER WAR DER BESTE? AB IN DIE KOMMENTARE")
        dt.append(f"drawtext=fontfile={FONT}:textfile={cta}:fontsize=44:fontcolor=black:"
                  f"box=1:boxcolor={AKZENT}:boxborderw=20:x=(w-tw)/2:y=1735:enable='gte(t,{max(0,d-4)})'")
    f.append("[v0]" + ",".join(dt) + ",format=yuv420p[v]")
    f.append("[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,"
             "aresample=48000[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(d), "-i", clip["datei"],
           "-filter_complex", ";".join(f), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out]
    subprocess.run(cmd, check=True)
    return d


def main():
    plan = json.load(open(sys.argv[1], encoding="utf-8"))
    ziel = sys.argv[2]
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    assert len(plan["clips"]) == 5, "Genau 5 Clips (Platz 5 bis 1) nötig"
    for c in plan["clips"]:
        if not os.path.isabs(c["datei"]):
            c["datei"] = os.path.join(base, c["datei"])
    with tempfile.TemporaryDirectory() as tmp:
        teile, gesamt = [], 0.0
        for i, c in enumerate(plan["clips"]):
            p = os.path.join(tmp, f"seg{i}.mp4")
            gesamt += segment(plan, i, c, tmp, p, i == 4)
            teile.append(p)
        lst = txt(tmp, "list.txt", "".join(f"file '{p}'\n" for p in teile))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", "-movflags", "+faststart", ziel], check=True)
    print(f"Fertig: {ziel} ({gesamt:.1f} s)")
    if gesamt < 61:
        print("WARNUNG: kürzer als 1:01 – längere Clips wählen oder 'ende' erweitern!")


if __name__ == "__main__":
    main()
