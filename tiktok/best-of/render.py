#!/usr/bin/env python3
"""Baut aus 5 Clips ein fertiges TikTok-Video im festen Design „HIGHLIGHTS MOGDITV“.

Aufruf:
  python3 tiktok/best-of/render.py <plan.json> <ausgabe.mp4> [--vorschau]
  python3 tiktok/best-of/render.py --vorlage <titel> <ausgabe.png> [beispielbild]

Design (für ALLE Streamer gleich, Details in DESIGN.md), von oben nach unten:
  1. Nummerierung 1–5 untereinander, jede Zahl mit langer Linie fast bis zum rechten Rand;
     nach jedem Clip erscheint sein Kurztitel auf seiner Linie
  2. Titel (z. B. „DIE BESTEN ABUGOKU & ABDI MOMENTE“), weiß mit leichtem 3D-Effekt in Violett
  3. großes, hohes Videofenster mit dünnem violetten Rahmen und dezentem Wasserzeichen
  Hintergrund fast schwarz (dunkles Lila/Blau) mit dezentem violetten Licht. Keine Deko.
  Untertitel (Whisper) unten im Videofenster, ein wichtiges Wort hellviolett.
  61–100 Sekunden, 5 Clips, Countdown Platz 5 → 1.

plan.json: siehe 2026-11/zarbex.json. Pro Clip optional: "start"/"ende" (Sekunden),
"fokus_x" (0 = linker Bildrand, 0.5 = Mitte, 1 = rechts), "gelb": ["wort", ...].
"""
import json, os, re, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- festes Design ----------
W, H = 1080, 1920
KANAL = "HIGHLIGHTS MOGDITV"
FONTDIR = "/usr/share/fonts/opentype/inter"
FONT_TITEL = f"{FONTDIR}/InterDisplay-Black.otf"
FONT_ZAHL = f"{FONTDIR}/InterDisplay-Black.otf"
FONT_LABEL = f"{FONTDIR}/InterDisplay-Bold.otf"
FONT_WZ = f"{FONTDIR}/InterDisplay-SemiBold.otf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

BG_OBEN, BG_MITTE, BG_UNTEN = (10, 7, 20), (15, 10, 30), (7, 6, 14)
VIOLETT = (139, 92, 246)          # Rahmen, Linien
VIOLETT_HELL = (196, 181, 253)    # Zahlen, Akzent-Wort in Untertiteln
VIOLETT_DUNKEL = (59, 31, 120)    # 3D-Kante des Titels
WEISS = (245, 243, 255)
AKZENT_ASS = "&H00FDB5C4&"        # VIOLETT_HELL als ASS-Farbe (BGR)

RAND_X = 28                        # seitlicher Abstand Videofenster
LISTE_Y, LISTE_ROW = 150, 76       # Nummerierung: Start + Zeilenhöhe
ZAHL_SIZE, LABEL_SIZE = 52, 44
LINIE_X0, LINIE_X1 = 118, 1040
TITEL_SIZE, TITEL_MAXW = 70, 1000
FENSTER_UNTEN = 1640               # Unterkante Videofenster (darunter nur Hintergrund)
RADIUS = 22
SUB_SIZE = 62
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
            img = _emoji_bild(run, font.size * 0.95)
            w += (img.width + 8) if img else 0
        else:
            w += font.getlength(run)
    return w


def _zeichne(img, x, y_base, text, font, fill, stroke=0, stroke_fill=(0, 0, 0)):
    d = ImageDraw.Draw(img)
    for e, run in _runs(text):
        if e:
            em = _emoji_bild(run, font.size * 0.95)
            if em:
                img.alpha_composite(em, (int(x + 4), int(y_base - em.height * 0.88)))
                x += em.width + 8
        else:
            d.text((x, y_base), run, font=font, fill=fill, stroke_width=stroke,
                   stroke_fill=stroke_fill, anchor="ls")
            x += font.getlength(run)


def _umbrechen(text, font, maxw):
    """Zeilen möglichst gleich lang (sieht ruhiger aus als „alles in Zeile 1“)."""
    woerter = text.split()
    if _breite(text, font) <= maxw:
        return [text]
    best = None
    for i in range(1, len(woerter)):
        a, b = " ".join(woerter[:i]), " ".join(woerter[i:])
        wa, wb = _breite(a, font), _breite(b, font)
        if max(wa, wb) <= maxw and (best is None or abs(wa - wb) < best[0]):
            best = (abs(wa - wb), [a, b])
    return best[1] if best else None


# ---------- Layout ----------
def layout(titel):
    titel = titel.upper()
    size = TITEL_SIZE
    while True:
        font = ImageFont.truetype(FONT_TITEL, size)
        zeilen = _umbrechen(titel, font, TITEL_MAXW)
        if zeilen or size <= 44:
            break
        size -= 4
    zeilen = zeilen or [titel]
    lh = int(size * 1.12)
    titel_y = LISTE_Y + LISTE_ROW * 5 + 34          # Oberkante Titelblock
    fenster_y = titel_y + lh * len(zeilen) + 36
    return dict(font=font, zeilen=zeilen, lh=lh, titel_y=titel_y,
                fx=RAND_X, fy=fenster_y, fw=W - 2 * RAND_X, fh=FENSTER_UNTEN - fenster_y)


def _glow(img, cx, cy, r, farbe, alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), fill=farbe + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.45)))


def hintergrund(titel, pfad):
    """Unterste Ebene: Verlauf, Licht, Nummerierung mit Linien, 3D-Titel."""
    L = layout(titel)
    y = np.linspace(0, 1, H)[:, None]
    oben, mitte, unten = (np.array(c, float) for c in (BG_OBEN, BG_MITTE, BG_UNTEN))
    grad = np.where(y < 0.45, oben + (mitte - oben) * (y / 0.45),
                    mitte + (unten - mitte) * ((y - 0.45) / 0.55))
    arr = np.repeat(grad[:, None, :], W, axis=1).reshape(H, W, 3)
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    # dezentes violettes Licht: hinter dem Titel, oben rechts, unten links
    _glow(img, W // 2, L["titel_y"] + L["lh"], 520, VIOLETT, 60)
    _glow(img, W - 80, 120, 380, VIOLETT, 28)
    _glow(img, 120, FENSTER_UNTEN - 100, 420, (76, 29, 149), 40)
    d = ImageDraw.Draw(img)
    # Nummerierung 1–5 untereinander mit langen Linien
    zf = ImageFont.truetype(FONT_ZAHL, ZAHL_SIZE)
    for platz in range(1, 6):
        yb = LISTE_Y + LISTE_ROW * platz - 18
        _zeichne(img, 52, yb, str(platz), zf, VIOLETT_HELL)
        ly = yb + 14
        for x in range(LINIE_X0, LINIE_X1):          # Linie, nach rechts leicht ausblendend
            a = int(150 - 90 * (x - LINIE_X0) / (LINIE_X1 - LINIE_X0))
            d.point((x, ly), fill=VIOLETT + (a,))
            d.point((x, ly + 1), fill=VIOLETT + (a // 2,))
    # dünne Trennlinie zwischen Liste und Titel
    ty = L["titel_y"] - 18
    d.line((W // 2 - 60, ty, W // 2 + 60, ty), fill=VIOLETT + (200,), width=3)
    # Titel mit leichtem 3D-Effekt (violette Kante nach rechts unten)
    f = L["font"]
    for i, z in enumerate(L["zeilen"]):
        x = (W - _breite(z, f)) / 2
        yb = L["titel_y"] + L["lh"] * (i + 1) - int(L["lh"] * 0.2)
        schatten = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _zeichne(schatten, x + 4, yb + 10, z, f, (0, 0, 0, 170))
        img.alpha_composite(schatten.filter(ImageFilter.GaussianBlur(6)))
        for k in range(6, 0, -1):
            _zeichne(img, x + k * 0.7, yb + k, z, f, VIOLETT_DUNKEL)
        _zeichne(img, x, yb, z, f, WEISS, 2, VIOLETT)
    img.convert("RGB").save(pfad)
    return img


def deckebene(titel, labels, aufgedeckt, pfad, bg=None):
    """Oberste Ebene: abgerundete Ecken + Rahmen + Wasserzeichen + sichtbare Kurztitel."""
    L = layout(titel)
    bg = bg or Image.open(hintergrund_cache(titel)).convert("RGBA")
    fx, fy, fw, fh = L["fx"], L["fy"], L["fw"], L["fh"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Ecken außerhalb der Rundung mit Hintergrund füllen
    maske = Image.new("L", (W, H), 255)
    ImageDraw.Draw(maske).rounded_rectangle((fx, fy, fx + fw - 1, fy + fh - 1), RADIUS, fill=0)
    box = Image.new("L", (W, H), 0)
    ImageDraw.Draw(box).rectangle((fx, fy, fx + fw, fy + fh), fill=255)
    from PIL import ImageChops
    img.paste(bg, (0, 0), ImageChops.multiply(maske, box))
    # leichter Glow + dünner Rahmen
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((fx - 2, fy - 2, fx + fw + 1, fy + fh + 1), RADIUS + 2,
                                           outline=VIOLETT + (150,), width=6)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(img).rounded_rectangle((fx, fy, fx + fw - 1, fy + fh - 1), RADIUS,
                                          outline=VIOLETT + (255,), width=3)
    # Wasserzeichen mittig, dezent
    wf = ImageFont.truetype(FONT_WZ, 46)
    text = " ".join(KANAL)                         # gesperrt
    wz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wz).text((fx + fw / 2, fy + fh / 2), text, font=wf, fill=(255, 255, 255, 46),
                            anchor="mm", stroke_width=1, stroke_fill=(0, 0, 0, 30))
    img.alpha_composite(wz)
    # Kurztitel auf den Linien
    lf = ImageFont.truetype(FONT_LABEL, LABEL_SIZE)
    for platz in range(1, 6):
        if platz in aufgedeckt and labels.get(platz):
            yb = LISTE_Y + LISTE_ROW * platz - 22
            _zeichne(img, LINIE_X0 + 14, yb, labels[platz], lf, WEISS, 3, (10, 6, 22))
    img.save(pfad)


_bg_cache = {}


def hintergrund_cache(titel):
    if titel not in _bg_cache:
        p = os.path.join(tempfile.gettempdir(), f"mogditv_bg_{abs(hash(titel))}.png")
        hintergrund(titel, p)
        _bg_cache[titel] = p
    return _bg_cache[titel]


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
    platz, d, L = clip["platz"], e - s, layout(plan["titel"])
    labels = {c["platz"]: c["label"] for c in plan["clips"]}
    vorher = {c["platz"] for c in plan["clips"] if c["platz"] > platz}
    bg = hintergrund_cache(plan["titel"])
    p1, p2, ass = f"{tmp}/o{i}a.png", f"{tmp}/o{i}b.png", f"{tmp}/s{i}.ass"
    deckebene(plan["titel"], labels, vorher, p1)
    deckebene(plan["titel"], labels, vorher | {platz}, p2)
    untertitel_ass(woerter(clip["datei"]) if plan.get("untertitel", True) else [], s, d,
                   clip.get("gelb", []) + plan.get("gelb", []), ass,
                   plan.get("cta", "WELCHER WAR AM {BESTEN}?\\NAB IN DIE KOMMENTARE") if platz == 1 else None, L)
    fw, fh, fokus = L["fw"], L["fh"], clip.get("fokus_x", 0.5)
    f = ";".join([
        f"[0:v]fps=30,setsar=1,scale={fw}:{fh}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={fw}:{fh}:'(iw-{fw})*{fokus}':'(ih-{fh})/2'[fg]",
        "[1:v]format=rgba[bg]",
        f"[bg][fg]overlay={L['fx']}:{L['fy']}[v0]",
        "[v0][2:v]overlay=0:0[v1]",
        f"[v1][3:v]overlay=0:0:enable='gte(t,{max(0, d - REVEAL_S):.2f})'[v2]",
        f"[v2]subtitles={ass}:fontsdir={FONTDIR},format=yuv420p[v]",
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
    ])
    q = ["-preset", "veryfast", "-crf", "23"] if vorschau else ["-preset", "medium", "-crf", "18"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-t", f"{d:.2f}", "-i", clip["datei"],
                    "-loop", "1", "-i", bg, "-loop", "1", "-i", p1, "-loop", "1", "-i", p2,
                    "-filter_complex", f, "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}",
                    "-c:v", "libx264", *q, "-profile:v", "high", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)


def vorlage(titel, ziel, beispiel=None, labels=None):
    """Statisches Muster-Bild (für Vorschau/Abnahme des Designs)."""
    L = layout(titel)
    bg = hintergrund(titel, ziel)
    if beispiel:
        b = Image.open(beispiel).convert("RGBA")
        f = max(L["fw"] / b.width, L["fh"] / b.height)
        b = b.resize((int(b.width * f) + 1, int(b.height * f) + 1), Image.LANCZOS)
        b = b.crop(((b.width - L["fw"]) // 2, (b.height - L["fh"]) // 2,
                    (b.width - L["fw"]) // 2 + L["fw"], (b.height - L["fh"]) // 2 + L["fh"]))
        bg.alpha_composite(b, (L["fx"], L["fy"]))
    else:
        leer = Image.new("RGBA", (L["fw"], L["fh"]), (18, 13, 32, 255))
        bg.alpha_composite(leer, (L["fx"], L["fy"]))
    tmp = ziel + ".deck.png"
    labels = labels or {}
    deckebene(titel, labels, set(labels), tmp, bg=Image.open(hintergrund_cache(titel)).convert("RGBA"))
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
