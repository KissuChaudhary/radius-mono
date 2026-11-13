"""
Radius Mono launch film: 16 s, 1920x1080, 30 fps, H.264 + AAC (synthesized sound design).

    python tools/video.py            -> media/radius-mono-launch.mp4 (master) + site-ready encodes

Scenes
  1  0.0-2.4  typewriter "Radius Mono", sharp (ROND 0)
  2  2.4-5.2  a ROND slider appears and rounds the word 0 -> 100
  3  5.2-9.0  candy glyph parade, weight + roundness waves
  4  9.0-12.8 code editor, a sweep line rounds the code
  5 12.8-16.0 end card
"""
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from textrender import Face, composite  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "media"
OUT.mkdir(exist_ok=True)
W, H, FPS, DUR = 1920, 1080, 30, 16.0
N = int(FPS * DUR)

UP = Face(str(ROOT / "fonts" / "variable" / "RadiusMono[ROND,wght].ttf"))
IT = Face(str(ROOT / "fonts" / "variable" / "RadiusMono-Italic[ROND,wght].ttf"))

WHITE = (244, 244, 245)
GRAY = (122, 122, 128)
DIM = (62, 62, 68)
PANEL = (12, 12, 13)
EDGE = (34, 34, 38)
ACCENT = (255, 122, 82)
CANDY = [(255, 77, 141), (43, 214, 123), (61, 123, 255), (255, 159, 28), (163, 91, 255), (255, 214, 10)]
SYN = {"k": (183, 155, 255), "s": (127, 214, 164), "n": (255, 179, 138), "c": (98, 104, 116), "f": (124, 183, 255), "t": (255, 141, 184), None: (226, 226, 230)}


# ---------------------------------------------------------------- helpers
def clamp01(t):
    return max(0.0, min(1.0, t))


def ease(t):
    t = clamp01(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def span(f, a, b):
    """Progress 0..1 of frame f within seconds [a, b]."""
    return clamp01((f / FPS - a) / (b - a))


_rr = {}


def rrect(w, h, r):
    key = (int(w), int(h), int(r))
    if key in _rr:
        return _rr[key]
    w, h, r = key
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    qx = np.abs(xx - w / 2) - (w / 2 - r)
    qy = np.abs(yy - h / 2) - (h / 2 - r)
    d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r
    m = np.clip(0.5 - d, 0, 1).astype(np.float32)
    _rr[key] = m
    return m


def outline(w, h, r, t=2):
    outer = rrect(w, h, r)
    inner = np.zeros_like(outer)
    inner[t : h - t, t : w - t] = rrect(w - 2 * t, h - 2 * t, max(1, r - t))
    return np.clip(outer - inner, 0, 1)


def text_center(c, face, s, size, cx, cy, color, rond=100, wght=400, alpha=1.0, clip=None):
    m, asc, adv = face.mask(s, size, rond, wght)
    x = cx - adv / 2
    y = cy - asc * 0.72  # optical: centre on x-height-ish band
    composite(c, m, x, y, color, alpha, clip)
    return x, y, adv, m


# ---------------------------------------------------------------- scenes
WORD = "Radius Mono"
WORD_SIZE = 230


def scene_type(c, f):
    t = f / FPS
    typed = min(len(WORD), max(0, int((t - 0.3) / 0.11) + 1)) if t >= 0.3 else 0
    m_full, asc, adv = UP.mask(WORD, WORD_SIZE, 0, 700)
    x0 = W / 2 - adv / 2
    y0 = H / 2 - asc * 0.72 - 40
    if typed:
        m, _, a = UP.mask(WORD[:typed], WORD_SIZE, 0, 700)
        composite(c, m, x0, y0, WHITE)
    else:
        a = 0
    # caret (rounded bar) blinks after typing
    blink = (int(t * 2.2) % 2 == 0) or typed < len(WORD)
    if blink and t < 2.5:
        cm = rrect(16, int(WORD_SIZE * 0.78), 8)
        composite(c, cm, x0 + a + 10, y0 + asc - WORD_SIZE * 0.74, ACCENT)


def word_and_slider(c, f, rond, slider_alpha, word_alpha=1.0):
    m, asc, adv = UP.mask(WORD, WORD_SIZE, rond, 700)
    composite(c, m, W / 2 - adv / 2, H / 2 - asc * 0.72 - 40, WHITE, word_alpha)
    if slider_alpha <= 0:
        return
    a = slider_alpha
    tw, ty = 760, 760
    tx = W / 2 - tw / 2
    composite(c, rrect(tw, 10, 5), tx, ty - 5, DIM, a)
    fill = int(tw * rond / 100)
    if fill > 10:
        composite(c, rrect(fill, 10, 5), tx, ty - 5, ACCENT, a)
    composite(c, rrect(40, 40, 20), tx + fill - 20, ty - 20, WHITE, a)
    lab, la, ladv = UP.mask('"ROND"', 36, 100, 600)
    composite(c, lab, tx - ladv - 34, ty - la * 0.62, GRAY, a)
    val, va, vadv = UP.mask(f"{int(round(rond)):>3}", 36, 100, 700)
    composite(c, val, tx + tw + 34, ty - va * 0.62, WHITE, a)


def scene_slider(c, f):
    t = f / FPS
    k = ease(span(f, 3.0, 4.8))
    rond = 100 * k
    word_and_slider(c, f, rond, ease_out(span(f, 2.4, 2.8)))


GLYPHS = ["R", "g", "{", "->", "&", "?"]


def scene_parade(c, f):
    t = f / FPS
    n = len(GLYPHS)
    cell = 236
    total = cell * (n + 1)  # "->" takes two cells
    x = W / 2 - total / 2
    for i, g in enumerate(GLYPHS):
        width = cell * (2 if g == "->" else 1)
        pop = ease_out(span(f, 5.3 + i * 0.12, 5.75 + i * 0.12))
        phase = (t - 6.2) * 1.6 - i * 0.55
        wv = 0.5 - 0.5 * math.cos(max(0.0, phase) * math.pi) if t > 6.2 else 0.0
        wght = 100 + 700 * (1 - wv) if t > 6.2 else 800
        rond = 100 * (0.5 + 0.5 * math.cos(max(0.0, phase - 0.4) * math.pi * 0.8)) if t > 6.2 else 100
        size = 300 * (0.82 + 0.18 * pop)
        m, asc, adv = UP.mask(g, size, rond, wght)
        cx = x + width / 2
        composite(c, m, cx - adv / 2, H / 2 - asc * 0.7 - 30, CANDY[i], pop)
        x += width
    cap_a = ease_out(span(f, 6.4, 6.9))
    text_center(c, UP, "wght 100-800   ROND 0-100   upright + italic", 34, W / 2, 880, GRAY, 100, 500, cap_a)


CODE = [
    [("c", "// fillet.ts")],
    [("k", "export function"), (None, " "), ("f", "fillet"), (None, "(c: "), ("t", "Corner"), (None, ", rond = "), ("n", "100"), (None, ") {")],
    [(None, "  "), ("k", "if"), (None, " (rond <= "), ("n", "0"), (None, " || c.hidden) "), ("k", "return"), (None, " "), ("n", "0"), (None, ";")],
    [(None, "  "), ("k", "const"), (None, " r = (rond / "), ("n", "100"), (None, ") * stem / "), ("n", "2"), (None, ";")],
    [(None, "  "), ("k", "return"), (None, " c.turn >= Math.PI ? r : r * "), ("f", "tan"), (None, "(c.turn / "), ("n", "2"), (None, ");")],
    [(None, "}")],
    [],
    [(None, "corners."), ("f", "filter"), (None, "((c) => c.hidden !== "), ("k", "true"), (None, ").length; "), ("c", "// 9728")],
]


def draw_code(c, rond, x0, y0, size, clip, alpha):
    lh = size * 1.62
    for li, line in enumerate(CODE):
        x = x0
        for cls, s in line:
            m, asc, adv = UP.mask(s, size, rond, 500)
            composite(c, m, x, y0 + li * lh, SYN[cls], alpha, clip)
            x += adv


def scene_code(c, f):
    a = ease_out(span(f, 9.0, 9.45))
    pw, ph = 1480, 640
    px, py = W / 2 - pw / 2, 250
    composite(c, rrect(pw, ph, 28), px, py, PANEL, a)
    composite(c, outline(pw, ph, 28, 2), px, py, EDGE, a)
    for i in range(3):
        composite(c, rrect(16, 16, 8), px + 30 + i * 28, py + 28, DIM, a)
    fm, fa, fadv = UP.mask("fillet.ts", 26, 100, 500)
    composite(c, fm, px + 130, py + 21, GRAY, a)
    composite(c, rrect(pw - 4, 2, 1), px + 2, py + 74, EDGE, a)
    sweep = ease(span(f, 9.7, 11.9))
    lx = px + 40 + (pw - 80) * sweep
    code_x, code_y, size = px + 56, py + 110, 36
    draw_code(c, 100, code_x, code_y, size, (px, lx), a)
    draw_code(c, 0, code_x, code_y, size, (lx, px + pw), a)
    if 0 < sweep < 1:
        composite(c, rrect(4, ph - 90, 2), lx - 2, py + 82, ACCENT, a)
        composite(c, rrect(44, 44, 22), lx - 22, py + ph / 2 + 20, ACCENT, a)
    cap = ease_out(span(f, 9.3, 9.8))
    text_center(c, UP, "Same metrics. Same 153 ligatures. Rounder.", 40, W / 2, 168, WHITE, 100, 600, cap)


def scene_end(c, f):
    a = ease_out(span(f, 12.8, 13.4))
    s = 0.94 + 0.06 * a
    m, asc, adv = UP.mask(WORD, 210 * s, 100, 800)
    composite(c, m, W / 2 - adv / 2, 330 - asc * 0.4, WHITE, a)
    b = ease_out(span(f, 13.2, 13.8))
    tm, ta, tadv = IT.mask("JetBrains Mono, with a border-radius.", 50, 100, 400)
    composite(c, tm, W / 2 - tadv / 2, 590, GRAY, b)
    chips = ["Free & open source", "ROND 0-100", "8 weights + italic", "153 ligatures"]
    sizes = [UP.mask(t, 28, 100, 500) for t in chips]
    widths = [adv + 56 for _, _, adv in sizes]
    gap = 18
    x = W / 2 - (sum(widths) + gap * (len(chips) - 1)) / 2
    for i, ((m2, a2, adv2), w) in enumerate(zip(sizes, widths)):
        ca = ease_out(span(f, 13.6 + i * 0.12, 14.1 + i * 0.12))
        composite(c, outline(int(w), 64, 32, 2), x, 730, EDGE, ca)
        composite(c, m2, x + 28, 730 + 32 - a2 * 0.68, WHITE if i == 0 else GRAY, ca)
        x += w + gap


def render_frame(f):
    c = np.zeros((H, W, 3), np.float32)
    t = f / FPS
    # cross-fades between scenes
    if t < 2.4:
        scene_type(c, f)
    elif t < 5.2:
        if t < 2.5:
            scene_type(c, f)
        scene_slider(c, f)
    if 5.0 <= t < 5.45:
        fade = 1 - ease_out(span(f, 5.0, 5.4))
        word_and_slider(c, f, 100, fade, fade)
    if 5.2 <= t < 9.3:
        layer = np.zeros_like(c)
        scene_parade(layer, f)
        k = 1 - ease_out(span(f, 8.8, 9.2))
        c += layer * k
    if 9.0 <= t < 13.0:
        layer = np.zeros_like(c)
        scene_code(layer, f)
        k = 1 - ease_out(span(f, 12.5, 12.9))
        c += layer * k
    if t >= 12.8:
        scene_end(c, f)
    return np.clip(c, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sound
SR = 44100


def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def tone(freq, dur, decay, partials=((1, 1.0),)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(amp * np.sin(2 * np.pi * freq * mul * t) * np.exp(-t * (1 + mul * 0.6) / decay) for mul, amp in partials)
    return s * env(n, 0.002, 10)


def place(track, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    j = min(len(track), i + len(sig))
    if j <= i:
        return
    l, r = (1 - max(0, pan)) * gain, (1 + min(0, pan)) * gain
    track[i:j, 0] += sig[: j - i] * l
    track[i:j, 1] += sig[: j - i] * r


def lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def soundtrack(path):
    rng = np.random.default_rng(7)
    tr = np.zeros((int(DUR * SR) + SR, 2), np.float32)
    # key clicks while typing
    for i in range(len(WORD)):
        n = int(0.035 * SR)
        noise = rng.standard_normal(n).astype(np.float32)
        click = np.diff(noise, prepend=0) * env(n, 0.0005, 0.008)
        place(tr, click * 0.22, 0.3 + i * 0.11, 1.0, rng.uniform(-0.3, 0.3))
    # whoosh while the knob travels
    n = int(1.9 * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    shaped = lowpass(noise, 0.08) * np.sin(np.linspace(0, np.pi, n)) ** 2
    place(tr, shaped * 0.9, 2.95)
    place(tr, tone(1046.5, 0.4, 0.12, ((1, 1), (2, 0.2))) * 0.18, 4.8)  # settle tick
    # marimba plucks for the parade (C major pentatonic)
    notes = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    for i, fq in enumerate(notes):
        place(tr, tone(fq, 1.2, 0.35, ((1, 1.0), (3.9, 0.35), (9.2, 0.08))) * 0.22, 5.3 + i * 0.12, 1.0, -0.4 + i * 0.16)
    # sweep for the code wipe
    n = int(2.3 * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    shaped = lowpass(noise, 0.03) * np.sin(np.linspace(0, np.pi, n)) ** 2
    place(tr, shaped * 1.2, 9.65)
    # end chord (Cmaj9), soft
    for fq in (130.81, 196.0, 246.94, 293.66, 329.63):
        n = int(3.2 * SR)
        t = np.arange(n) / SR
        pad = np.sin(2 * np.pi * fq * t) * np.clip(t / 0.25, 0, 1) * np.exp(-t / 1.6)
        place(tr, pad.astype(np.float32) * 0.07, 12.85)
    tr = tr[: int(DUR * SR)]
    tr /= max(1e-6, np.abs(tr).max()) / 0.8
    pcm = (tr * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- encode
def main():
    wav = OUT / "soundtrack.wav"
    soundtrack(wav)
    master = OUT / "radius-mono-launch.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(master),
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(N):
        p.stdin.write(render_frame(f).tobytes())
        if f % 60 == 0:
            print(f"frame {f}/{N}", flush=True)
    p.stdin.close()
    p.wait()
    # poster frames for the site / social cards
    from PIL import Image

    Image.fromarray(render_frame(int(15.5 * FPS))).save(OUT / "poster.jpg", quality=90)
    Image.fromarray(render_frame(int(7.0 * FPS))).save(OUT / "frame-parade.jpg", quality=90)
    Image.fromarray(render_frame(int(11.0 * FPS))).save(OUT / "frame-code.jpg", quality=90)
    # web encode (smaller), muted-friendly but keeps audio
    web = OUT / "radius-mono-launch-web.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(master), "-vf", "scale=1600:-2",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(web)], check=True)
    for pth in (master, web):
        print(pth, f"{pth.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--frames":
        from PIL import Image

        for s in sys.argv[2:]:
            Image.fromarray(render_frame(int(float(s) * FPS))).save(OUT / f"test-{s}.jpg", quality=88)
            print(OUT / f"test-{s}.jpg")
    else:
        main()
