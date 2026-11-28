#!/usr/bin/env python3
"""Baut aus 5 Clips ein fertiges TikTok-Video im festen Design „HIGHLIGHTS MOGDITV“.

Aufruf:
  python3 tiktok/best-of/render.py <plan.json> <ausgabe.mp4> [--vorschau]
  python3 tiktok/best-of/render.py --vorlage "<titel>" <ausgabe.png> [beispielbild]

Design (Makis Designbriefing vom 29.11.2026, Details in DESIGN.md), von oben nach unten:
  1. Überschrift „STREAMER CLIP UND BEST OFS“: rot, weißer Rand, Schatten, leicht gebogen;
     darunter klein „HIGHLIGHTS MOGDITV“
  2. großes, waagerechtes Videofenster (16:9) mit dünnem, dezent violettem Rahmen;
     mittig ein sehr dezentes Wasserzeichen in dunklem Violett
  3. Video-Titel zweizeilig, weiß, fett, kursiv, schwarzer Schatten, violetter Akzent
  4. Rangliste 1–5 untereinander, links, weiß kursiv; „1“ leicht hervorgehoben.
     Nach jedem Clip erscheint sein Kurztitel neben seiner Zahl.
  Hintergrund: derselbe Clip vergrößert, stark verschwommen, dunkel-violett eingefärbt.
  Untertitel (Whisper) unten im Videofenster. 61–100 Sekunden, Countdown Platz 5 → 1.

plan.json: siehe 2026-11/zarbex.json. Pro Clip optional: "start"/"ende" (Sekunden),
"gelb": ["wort", ...] (Wörter, die in den Untertiteln hervorgehoben werden).
"""
import json, math, os, re, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- festes Design ----------
W, H = 1080, 1920
KANAL = "HIGHLIGHTS MOGDITV"
KOPF_TEXT = "STREAMER CLIP UND BEST OFS"
FONTDIR = "/usr/share/fonts/opentype/inter"
F_KOPF = f"{FONTDIR}/InterDisplay-BlackItalic.otf"
F_TITEL = f"{FONTDIR}/InterDisplay-BlackItalic.otf"
F_ZAHL = f"{FONTDIR}/InterDisplay-BlackItalic.otf"
F_LABEL = f"{FONTDIR}/InterDisplay-ExtraBoldItalic.otf"
F_KLEIN = f"{FONTDIR}/InterDisplay-SemiBold.otf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

ROT = (226, 32, 44)
WEISS = (255, 255, 255)
SCHWARZ = (0, 0, 0)
VIOLETT = (139, 92, 246)           # Rahmen, Akzente
VIOLETT_HELL = (196, 181, 253)     # Hervorhebung „1“, Akzentwort in Untertiteln
VIOLETT_DUNKEL = (76, 29, 149)     # Wasserzeichen
TOENUNG = "0x14082A"               # Einfärbung des verschwommenen Hintergrunds
TOENUNG_ALPHA = 0.62
AKZENT_ASS = "&H00FDB5C4&"         # VIOLETT_HELL als ASS-Farbe (BGR)

KOPF_Y, KOPF_SIZE, KOPF_BOGEN = 120, 70, 2600   # Bogen = Radius (größer = flacher)
KLEIN_Y = 238
FX, FY, FW = 24, 290, W - 48       # Videofenster
FH = round(FW * 9 / 16)            # 16:9 → 581 px hoch
TITEL_Y, TITEL_SIZE = FY + FH + 44, 74
LISTE_Y, LISTE_ROW = 1150, 132     # Rangliste reicht bis ca. 1800
ZAHL_SIZE, LABEL_SIZE = 92, 52
SUB_SIZE = 56
MIN_S, MAX_S, ZIEL_S = 61, 100, 95
REVEAL_S = 1.2
CTA_S = 3.0
HYPE = {"digger", "alter", "bruder", "was", "nein", "krass", "psycho", "wtf", "geil", "junge",
        "wallah", "safe", "never", "hilfe", "tot", "brutal"}

_model = None


# ---------- Text mit Emojis ----------
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
            img = _emoji_bild(run, font.size * 0.9)
            w += (img.width + 8) if img else 0
        else:
            w += font.getlength(run)
    return w


def _zeichne(img, x, y_base, text, font, fill, stroke=0, stroke_fill=SCHWARZ):
    d = ImageDraw.Draw(img)
    for e, run in _runs(text):
        if e:
            em = _emoji_bild(run, font.size * 0.9)
            if em:
                img.alpha_composite(em, (int(x + 4), int(y_base - em.height * 0.9)))
                x += em.width + 8
        else:
            d.text((x, y_base), run, font=font, fill=fill, stroke_width=stroke,
                   stroke_fill=stroke_fill, anchor="ls")
            x += font.getlength(run)


def _mit_schatten(img, x, y, text, font, fill, stroke=0, stroke_fill=SCHWARZ, dx=4, dy=6, blur=5, alpha=200):
    sch = Image.new("RGBA", img.size, (0, 0, 0, 0))
    _zeichne(sch, x + dx, y + dy, text, font, (0, 0, 0, alpha), stroke, (0, 0, 0, alpha))
    img.alpha_composite(sch.filter(ImageFilter.GaussianBlur(blur)))
    _zeichne(img, x, y, text, font, fill, stroke, stroke_fill)


def _zwei_zeilen(text, font, maxw):
    if _breite(text, font) <= maxw and len(text.split()) < 3:
        return [text]
    w = text.split()
    best = None
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        diff = abs(_breite(a, font) - _breite(b, font))
        if max(_breite(a, font), _breite(b, font)) <= maxw and (best is None or diff < best[0]):
            best = (diff, [a, b])
    return best[1] if best else None


# ---------- Ebenen ----------
def _kopfzeile(img):
    """Rote, leicht gebogene Überschrift mit weißem Rand und Schatten."""
    size = KOPF_SIZE
    font = ImageFont.truetype(F_KOPF, size)
    while font.getlength(KOPF_TEXT) > W - 90:
        size -= 2
        font = ImageFont.truetype(F_KOPF, size)
    R = KOPF_BOGEN
    gesamt = font.getlength(KOPF_TEXT)
    cx, cy = W / 2, KOPF_Y + size * 0.75 + R      # Kreismittelpunkt weit unterhalb
    pos = -gesamt / 2
    schatten = Image.new("RGBA", img.size, (0, 0, 0, 0))
    vorne = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for ch in KOPF_TEXT:
        adv = font.getlength(ch)
        winkel = (pos + adv / 2) / R
        x = cx + R * math.sin(winkel)
        y = cy - R * math.cos(winkel)
        for ebene, fill, stroke, off in ((schatten, (0, 0, 0, 210), (0, 0, 0, 210), (5, 8)),
                                         (vorne, ROT, WEISS, (0, 0))):
            c = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            ImageDraw.Draw(c).text((size, size), ch, font=font, fill=fill, anchor="ms",
                                   stroke_width=6, stroke_fill=stroke)
            c = c.rotate(-math.degrees(winkel), resample=Image.BICUBIC, center=(size, size))
            ebene.alpha_composite(c, (int(x - size + off[0]), int(y - size + off[1])))
        pos += adv
    img.alpha_composite(schatten.filter(ImageFilter.GaussianBlur(4)))
    img.alpha_composite(vorne)
    kf = ImageFont.truetype(F_KLEIN, 28)
    t = " ".join(KANAL)
    ImageDraw.Draw(img).text((W / 2, KLEIN_Y), t, font=kf, fill=(255, 255, 255, 190), anchor="mm")


def deckebene(titel, labels, aufgedeckt, pfad):
    """Alles außer Hintergrund und Clip (transparentes PNG, liegt über dem Video)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _kopfzeile(img)
    # Videofenster: dünner, dezenter violetter Rahmen + Wasserzeichen
    d = ImageDraw.Draw(img)
    d.rectangle((FX - 3, FY - 3, FX + FW + 2, FY + FH + 2), outline=VIOLETT + (230,), width=3)
    wf = ImageFont.truetype(F_KOPF, 60)
    wz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wz).text((FX + FW / 2, FY + FH / 2), KANAL, font=wf, fill=VIOLETT_DUNKEL + (70,),
                            anchor="mm", stroke_width=1, stroke_fill=(255, 255, 255, 18))
    img.alpha_composite(wz)
    # Titel unter dem Video: zweizeilig, weiß, kursiv, Schatten, violetter Akzent
    t = titel.upper()
    size = TITEL_SIZE
    while True:
        tf = ImageFont.truetype(F_TITEL, size)
        zeilen = _zwei_zeilen(t, tf, W - 80)
        if zeilen or size <= 46:
            break
        size -= 3
    zeilen = zeilen or [t]
    lh = int(size * 1.1)
    for i, z in enumerate(zeilen):
        x = (W - _breite(z, tf)) / 2
        yb = TITEL_Y + lh * (i + 1) - int(lh * 0.2)
        _mit_schatten(img, x, yb, z, tf, WEISS, 3, VIOLETT, dx=4, dy=7, blur=6, alpha=230)
    akzent_y = TITEL_Y + lh * len(zeilen) + 14
    d.rounded_rectangle((W / 2 - 70, akzent_y, W / 2 + 70, akzent_y + 5), 3, fill=VIOLETT + (255,))
    # Rangliste 1–5 untereinander
    zf = ImageFont.truetype(F_ZAHL, ZAHL_SIZE)
    lf = ImageFont.truetype(F_LABEL, LABEL_SIZE)
    for platz in range(1, 6):
        yb = LISTE_Y + LISTE_ROW * (platz - 1) + ZAHL_SIZE
        if platz == 1:
            _mit_schatten(img, 60, yb, "1.", zf, WEISS, 4, VIOLETT, alpha=230)
        else:
            _mit_schatten(img, 60, yb, f"{platz}.", zf, WEISS, 2, SCHWARZ, alpha=220)
        if platz in aufgedeckt and labels.get(platz):
            _mit_schatten(img, 190, yb - 14, labels[platz].upper(), lf, WEISS, 2, SCHWARZ, alpha=220)
    img.save(pfad)


def _toenung(pfad):
    r, g, b = (int(TOENUNG[i:i + 2], 16) for i in (2, 4, 6))
    Image.new("RGBA", (W, H), (r, g, b, int(255 * TOENUNG_ALPHA))).save(pfad)


# ---------- Untertitel ----------
def woerter(datei):
    cache = datei + ".woerter.json"
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(os.environ.get("WHISPER_MODELL", "small"), device="cpu",
                              compute_type="int8", download_root=os.path.expanduser("~/.cache/whisper"))
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


def untertitel_ass(ws, start, d, gelb, pfad, cta, L):
    unten = L["fy"] + L["fh"] - 70
    kopf = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Display Black,{SUB_SIZE},&H00FFFFFF,&H00FFFFFF,&H00160A0A,&H90000000,0,0,0,0,100,100,2,0,1,5,3,2,70,70,{H - unten},1

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
        b = min(ch[-1]["e"] + 0.35, chunks[i + 1][0]["s"] if i + 1 < len(chunks) else d, ende_sub)
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
        txt = " ".join(f"{{\\c{AKZENT_ASS}}}{x}{{\\c&H00FFFFFF&}}" if j == hi else x
                       for j, x in enumerate(wl))
        zeilen.append(f"Dialogue: 0,{_ass_zeit(a)},{_ass_zeit(b)},Sub,,0,0,0,,"
                      f"{{\\fscx88\\fscy88\\t(0,80,\\fscx100\\fscy100)}}{txt}")
    if cta:
        t = re.sub(r"\{(.+?)\}", lambda m: f"{{\\c{AKZENT_ASS}}}{m.group(1)}{{\\c&H00FFFFFF&}}", cta)
        zeilen.append(f"Dialogue: 0,{_ass_zeit(d - CTA_S)},{_ass_zeit(d)},Sub,,0,0,0,,{t}")
    open(pfad, "w", encoding="utf-8").write(kopf + "\n".join(zeilen) + "\n")


# ---------- Schnitt ----------
def dauer(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nw=1:nk=1", path]))


def fenster(plan):
    fs = [[c.get("start") or 0.0, c.get("ende") or dauer(c["datei"])] for c in plan["clips"]]
    if sum(e - s for s, e in fs) > MAX_S:            # vorne kürzen: Moment ist meist am Clip-Ende
        while sum(e - s for s, e in fs) > ZIEL_S:
            i = max(range(5), key=lambda i: fs[i][1] - fs[i][0])
            if fs[i][1] - fs[i][0] <= 10:
                break
            fs[i][0] += 0.5
    total = sum(e - s for s, e in fs)
    if not MIN_S <= total <= MAX_S:
        sys.exit(f"Gesamtlänge {total:.1f} s liegt nicht zwischen {MIN_S} und {MAX_S} s.")
    return fs


def segment(plan, i, clip, s, e, tmp, out, vorschau):
    platz, d = clip["platz"], e - s
    labels = {c["platz"]: c["label"] for c in plan["clips"]}
    vorher = {c["platz"] for c in plan["clips"] if c["platz"] > platz}
    p1, p2, ass, ton = f"{tmp}/o{i}a.png", f"{tmp}/o{i}b.png", f"{tmp}/s{i}.ass", f"{tmp}/ton.png"
    deckebene(plan["titel"], labels, vorher, p1)
    deckebene(plan["titel"], labels, vorher | {platz}, p2)
    _toenung(ton)
    untertitel_ass(woerter(clip["datei"]) if plan.get("untertitel", True) else [], s, d,
                   clip.get("gelb", []) + plan.get("gelb", []), ass,
                   plan.get("cta", "WELCHER WAR AM {BESTEN}?\\NAB IN DIE KOMMENTARE") if platz == 1 else None,
                   {"fy": FY, "fh": FH})
    f = ";".join([
        "[0:v]fps=30,setsar=1,split[a][b]",
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:6,"
        f"eq=brightness=-0.12:saturation=0.75[bg0]",
        "[bg0][1:v]overlay=0:0[bg]",
        f"[b]scale={FW}:{FH}:force_original_aspect_ratio=increase:flags=lanczos,crop={FW}:{FH}[fg]",
        f"[bg][fg]overlay={FX}:{FY}[v0]",
        "[v0][2:v]overlay=0:0[v1]",
        f"[v1][3:v]overlay=0:0:enable='gte(t,{max(0, d - REVEAL_S):.2f})'[v2]",
        f"[v2]subtitles={ass}:fontsdir={FONTDIR},format=yuv420p[v]",
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
    ])
    q = ["-preset", "veryfast", "-crf", "23"] if vorschau else ["-preset", "medium", "-crf", "18"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-t", f"{d:.2f}", "-i", clip["datei"],
                    "-loop", "1", "-i", ton, "-loop", "1", "-i", p1, "-loop", "1", "-i", p2,
                    "-filter_complex", f, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
                    "-c:v", "libx264", *q, "-profile:v", "high", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)


def vorlage(titel, ziel, beispiel=None, labels=None):
    """Statisches Muster-Bild des Designs (leer oder mit Beispielbild im Fenster)."""
    if beispiel:
        b = Image.open(beispiel).convert("RGB")
        f = max(W / b.width, H / b.height)
        bg = b.resize((int(b.width * f) + 1, int(b.height * f) + 1), Image.LANCZOS)
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W,
                      (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(40)).convert("RGBA")
        bg = Image.eval(bg, lambda v: int(v * 0.85))
        f = max(FW / b.width, FH / b.height)
        fg = b.resize((int(b.width * f) + 1, int(b.height * f) + 1), Image.LANCZOS)
        fg = fg.crop(((fg.width - FW) // 2, (fg.height - FH) // 2, (fg.width - FW) // 2 + FW,
                      (fg.height - FH) // 2 + FH))
    else:
        bg = Image.new("RGBA", (W, H), (30, 22, 48, 255))
        fg = Image.new("RGB", (FW, FH), (22, 16, 36))
    bg = bg.convert("RGBA")
    tmp = ziel + ".tmp.png"
    _toenung(tmp)
    bg.alpha_composite(Image.open(tmp))
    bg.paste(fg, (FX, FY))
    deckebene(titel, labels or {}, set(labels or {}), tmp)
    bg.alpha_composite(Image.open(tmp))
    os.remove(tmp)
    bg.convert("RGB").save(ziel)


def main():
    if sys.argv[1] == "--vorlage":
        vorlage(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
        return
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
        open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p in teile))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                        "-c", "copy", "-movflags", "+faststart", ziel], check=True)
    print(f"Fertig: {ziel} ({sum(e - s for s, e in fs):.1f} s)")


if __name__ == "__main__":
    main()
