#!/usr/bin/env python3
"""Baut aus 5 Clips ein fertiges TikTok-Video im festen Maini-Design „Top-5-Momente“.

Aufruf:  python3 tiktok/best-of/render.py <plan.json> <ausgabe.mp4> [--vorschau]

Design (für ALLE Streamer gleich, siehe DESIGN.md):
- 1080x1920 (9:16), 30 fps, 61–100 Sekunden, 5 Clips als Countdown Platz 5 → 1
- oben gelber, fetter Titel (z. B. „Zarbex' krasseste Momente in GTA 6 – Part 1“)
- darunter Liste 1.–5.: nach jedem Clip erscheint sein Kurztitel mit Emoji
- Clip mittig, Hintergrund = derselbe Clip verschwommen (keine schwarzen Balken)
- eingebrannte Untertitel (Whisper), wichtige Wörter gelb
- am Ende Frage an die Zuschauer („Welcher war am krassesten?“) → Kommentare

plan.json: siehe 2026-11/zarbex.json. Reihenfolge der Clips = Platz 5, 4, 3, 2, 1.
Pro Clip optional: "start"/"ende" (Sekunden im Clip), "gelb": ["wort", ...].
"""
import json, os, re, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------- festes Design ----------
W, H = 1080, 1920
FONTDIR = "/usr/share/fonts/opentype/inter"
FONT_TITEL = f"{FONTDIR}/InterDisplay-Black.otf"
FONT_LISTE = f"{FONTDIR}/InterDisplay-Black.otf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
GELB = (255, 210, 31)
GELB_ASS = "&H001FD2FF&"          # ASS-Farben sind BGR
TITEL_Y, TITEL_SIZE, TITEL_MAXW = 150, 74, 960
LISTE_SIZE, LISTE_ROW = 48, 64
VID_H = 760                        # Höhe des Clip-Fensters (leicht gezoomt)
SUB_SIZE = 64
MIN_S, MAX_S, ZIEL_S = 61, 100, 95
REVEAL_S = 1.2                     # Kurztitel erscheint so viele Sekunden vor Clip-Ende
CTA_S = 3.0
HYPE = {"digger", "alter", "bruder", "was", "nein", "krass", "psycho", "wtf", "geil", "junge",
        "wallah", "safe", "oh", "ah", "ey", "ja", "nee", "never", "hilfe", "tot", "brutal"}

_model = None


# ---------- Text mit Emojis (Pillow) ----------
def _ist_emoji(ch):
    cp = ord(ch)
    return cp >= 0x1F000 or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF or cp in (0xFE0F, 0x200D)


def _runs(text):
    out = []
    for ch in text:
        e = _ist_emoji(ch)
        if out and out[-1][0] == e:
            out[-1][1] += ch
        else:
            out.append([e, ch])
    return out


def _emoji_bild(run, hoehe):
    ef = ImageFont.truetype(FONT_EMOJI, 109)
    tmp = Image.new("RGBA", (109 * (len(run) + 1), 140), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((0, 0), run, font=ef, embedded_color=True)
    bb = tmp.getbbox()
    if not bb:
        return None
    tmp = tmp.crop(bb)
    f = hoehe / tmp.height
    return tmp.resize((max(1, int(tmp.width * f)), int(hoehe)), Image.LANCZOS)


def _breite(text, font):
    w = 0
    for e, run in _runs(text):
        if e:
            img = _emoji_bild(run, font.size * 0.95)
            w += (img.width + 8) if img else 0
        else:
            w += font.getlength(run)
    return w


def _zeichne(img, x, y_base, text, font, fill, stroke):
    d = ImageDraw.Draw(img)
    for e, run in _runs(text):
        if e:
            em = _emoji_bild(run, font.size * 0.95)
            if em:
                img.alpha_composite(em, (int(x + 4), int(y_base - em.height * 0.88)))
                x += em.width + 8
        else:
            d.text((x, y_base), run, font=font, fill=fill, stroke_width=stroke,
                   stroke_fill=(0, 0, 0), anchor="ls")
            x += font.getlength(run)


def _umbrechen(text, font, maxw):
    zeilen, z = [], ""
    for wort in text.split():
        t = (z + " " + wort).strip()
        if _breite(t, font) <= maxw or not z:
            z = t
        else:
            zeilen.append(z)
            z = wort
    return zeilen + ([z] if z else [])


def layout(titel):
    size = TITEL_SIZE
    while True:
        font = ImageFont.truetype(FONT_TITEL, size)
        zeilen = _umbrechen(titel, font, TITEL_MAXW)
        if len(zeilen) <= 2 or size <= 50:
            break
        size -= 4
    lh = int(size * 1.15)
    liste_y = TITEL_Y + lh * len(zeilen) + 40
    vid_y = liste_y + LISTE_ROW * 5 + 30
    return font, zeilen, lh, liste_y, vid_y


def overlay_png(plan, aufgedeckt, pfad):
    """Titel + Liste; `aufgedeckt` = Menge der Plätze, deren Kurztitel schon sichtbar ist."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    font, zeilen, lh, liste_y, _ = layout(plan["titel"])
    for i, z in enumerate(zeilen):
        _zeichne(img, (W - _breite(z, font)) / 2, TITEL_Y + lh * (i + 1) - int(lh * 0.22), z, font,
                 GELB, 7)
    lf = ImageFont.truetype(FONT_LISTE, LISTE_SIZE)
    labels = {c["platz"]: c["label"] for c in plan["clips"]}
    for platz in range(1, 6):
        yb = liste_y + LISTE_ROW * platz - 14
        _zeichne(img, 80, yb, f"{platz}.", lf, (255, 255, 255), 5)
        if platz in aufgedeckt:
            _zeichne(img, 160, yb, labels[platz], lf, (255, 255, 255), 5)
    img.save(pfad)


# ---------- Untertitel (Whisper) ----------
def woerter(datei):
    cache = datei + ".woerter.json"
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(os.environ.get("WHISPER_MODELL", "small"), device="cpu",
                              compute_type="int8",
                              download_root=os.path.expanduser("~/.cache/whisper"))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", datei, "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = _model.transcribe(audio, language="de", word_timestamps=True, vad_filter=True)
    ws = [{"s": round(w.start, 2), "e": round(w.end, 2), "w": w.word.strip()}
          for s in segs for w in (s.words or [])]
    json.dump(ws, open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return ws


def _ass_zeit(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _sauber(w):
    return re.sub(r"[^\wÄÖÜäöüß?!'-]", "", w).upper()


def untertitel_ass(ws, start, d, gelb, pfad, cta, vid_y):
    unten = vid_y + VID_H - 40                     # Untertitel im unteren Teil des Clips
    kopf = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Display Black,{SUB_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,2,0,1,6,2,2,60,60,{H - unten},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ende_sub = d - CTA_S if cta else d
    ws = [dict(w, s=w["s"] - start, e=w["e"] - start) for w in ws
          if w["e"] > start and w["s"] < start + d and _sauber(w["w"])]
    chunks, cur = [], []
    for w in ws:
        if cur and (len(cur) >= 3 or sum(len(x["w"]) for x in cur) > 15 or w["s"] - cur[-1]["e"] > 0.5):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    gelb = [g.lower() for g in gelb]
    zeilen = []
    for i, ch in enumerate(chunks):
        a = ch[0]["s"]
        b = min(ch[-1]["e"] + 0.35, chunks[i + 1][0]["s"] if i + 1 < len(chunks) else d)
        b = min(b, ende_sub)
        if b - a < 0.1:
            continue
        wl = [_sauber(w["w"]) for w in ch]
        low = [x.lower().strip("?!") for x in wl]
        hi = next((j for j, x in enumerate(low) if any(g in x for g in gelb)), None)
        if hi is None:
            hi = next((j for j, x in enumerate(low) if x in HYPE), None)
        if hi is None:
            j = max(range(len(low)), key=lambda j: len(low[j]))
            hi = j if len(low[j]) >= 5 else None
        txt = " ".join(f"{{\\c{GELB_ASS}}}{x}{{\\c&H00FFFFFF&}}" if j == hi else x
                       for j, x in enumerate(wl))
        # kleiner Pop-Effekt beim Erscheinen
        zeilen.append(f"Dialogue: 0,{_ass_zeit(a)},{_ass_zeit(b)},Sub,,0,0,0,,"
                      f"{{\\fscx85\\fscy85\\t(0,80,\\fscx100\\fscy100)}}{txt}")
    if cta:
        t = re.sub(r"\{(.+?)\}", lambda m: f"{{\\c{GELB_ASS}}}{m.group(1)}{{\\c&H00FFFFFF&}}", cta)
        zeilen.append(f"Dialogue: 0,{_ass_zeit(d - CTA_S)},{_ass_zeit(d)},Sub,,0,0,0,,{t}")
    open(pfad, "w", encoding="utf-8").write(kopf + "\n".join(zeilen) + "\n")


# ---------- Schnitt ----------
def dauer(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nw=1:nk=1", path]))


def fenster(plan):
    """Start/Ende je Clip; ist alles zusammen > 100 s, wird vorne an den längsten Clips gekürzt
    (bei Twitch-Clips passiert der Moment meist am Ende)."""
    fs = []
    for c in plan["clips"]:
        s = c.get("start") or 0.0
        e = c.get("ende") or dauer(c["datei"])
        fs.append([s, e])
    total = sum(e - s for s, e in fs)
    if total > MAX_S:
        while sum(e - s for s, e in fs) > ZIEL_S:
            i = max(range(5), key=lambda i: fs[i][1] - fs[i][0])
            if fs[i][1] - fs[i][0] <= 10:
                break
            fs[i][0] += 0.5
    total = sum(e - s for s, e in fs)
    if not MIN_S <= total <= MAX_S:
        sys.exit(f"Gesamtlänge {total:.1f} s liegt nicht zwischen {MIN_S} und {MAX_S} s – "
                 f"andere Clips wählen oder start/ende anpassen.")
    return fs


def segment(plan, i, clip, s, e, tmp, out, vorschau):
    platz = clip["platz"]
    d = e - s
    _, _, _, _, vid_y = layout(plan["titel"])
    vorher = {c["platz"] for c in plan["clips"] if c["platz"] > platz}
    p1, p2 = f"{tmp}/o{i}a.png", f"{tmp}/o{i}b.png"
    overlay_png(plan, vorher, p1)
    overlay_png(plan, vorher | {platz}, p2)
    ass = f"{tmp}/s{i}.ass"
    letzter = platz == 1
    untertitel_ass(woerter(clip["datei"]) if plan.get("untertitel", True) else [], s, d,
                   clip.get("gelb", []) + plan.get("gelb", []), ass,
                   plan.get("cta", "WELCHER WAR AM {KRANKSTEN}?\\NAB IN DIE KOMMENTARE") if letzter else None,
                   vid_y)
    f = ";".join([
        "[0:v]fps=30,setsar=1,split[a][b]",
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"boxblur=30:4,eq=brightness=-0.22:saturation=1.15[bg]",
        f"[b]crop='min(iw,ih*{W}/{VID_H})':'min(ih,iw*{VID_H}/{W})',scale={W}:{VID_H}:flags=lanczos[fg]",
        f"[bg][fg]overlay=0:{vid_y}[v0]",
        "[v0][1:v]overlay=0:0[v1]",
        f"[v1][2:v]overlay=0:0:enable='gte(t,{max(0, d - REVEAL_S):.2f})'[v2]",
        f"[v2]subtitles={ass}:fontsdir={FONTDIR},format=yuv420p[v]",
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,"
        "aresample=48000[a]",
    ])
    q = ["-preset", "veryfast", "-crf", "23"] if vorschau else ["-preset", "medium", "-crf", "18"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-t", f"{d:.2f}", "-i", clip["datei"],
                    "-loop", "1", "-i", p1, "-loop", "1", "-i", p2,
                    "-filter_complex", f, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
                    "-c:v", "libx264", *q, "-profile:v", "high", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)


def main():
    plan_pfad, ziel = sys.argv[1], sys.argv[2]
    vorschau = "--vorschau" in sys.argv
    plan = json.load(open(plan_pfad, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(plan_pfad))
    clips = sorted(plan["clips"], key=lambda c: -c["platz"])
    assert [c["platz"] for c in clips] == [5, 4, 3, 2, 1], "Genau 5 Clips mit Platz 5 bis 1 nötig"
    plan["clips"] = clips
    for c in clips:
        if not os.path.isabs(c["datei"]):
            c["datei"] = os.path.join(base, c["datei"])
        if not os.path.exists(c["datei"]):
            sys.exit(f"Clip fehlt: {c['datei']}  ({c.get('twitch', '')})")
    fs = fenster(plan)
    with tempfile.TemporaryDirectory() as tmp:
        teile = []
        for i, (c, (s, e)) in enumerate(zip(clips, fs)):
            print(f"Platz {c['platz']}: {c['label']}  ({s:.1f}–{e:.1f} s)", flush=True)
            p = f"{tmp}/seg{i}.mp4"
            segment(plan, i, c, s, e, tmp, p, vorschau)
            teile.append(p)
        lst = f"{tmp}/list.txt"
        open(lst, "w").write("".join(f"file '{p}'\n" for p in teile))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", "-movflags", "+faststart", ziel], check=True)
    print(f"Fertig: {ziel} ({sum(e - s for s, e in fs):.1f} s)")


if __name__ == "__main__":
    main()
