"""Launch visuals: docs/banner.png (static) and docs/morph.gif (ROND 0 -> 100 loop)."""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from hbrender import render  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONT = str(ROOT / "fonts" / "variable" / "RadiusMono[ROND,wght].ttf")
ITAL = str(ROOT / "fonts" / "variable" / "RadiusMono-Italic[ROND,wght].ttf")
BG = np.array([16, 18, 22], np.float32)
FG = np.array([236, 237, 239], np.float32)
MUTED = np.array([120, 127, 140], np.float32)
ACCENT = np.array([255, 122, 82], np.float32)
W, H = 1600, 840


def paste(canvas, mask, x, y, color):
    h, w = mask.shape
    h = min(h, canvas.shape[0] - y)
    w = min(w, canvas.shape[1] - x)
    m = mask[:h, :w, None]
    canvas[y : y + h, x : x + w] = canvas[y : y + h, x : x + w] * (1 - m) + color * m


def frame(rond, wght=800):
    c = np.tile(BG, (H, W, 1))
    paste(c, render(FONT, "Radius Mono", 190, {"ROND": rond, "wght": wght}), 70, 70, FG)
    paste(c, render(ITAL, "JetBrains Mono, with a border-radius.", 50, {"ROND": rond, "wght": 500}), 78, 330, MUTED)
    code = "const r = (x) => x ?? 0; // {} [] != ==="
    paste(c, render(FONT, code, 46, {"ROND": rond, "wght": 600}), 78, 470, FG)
    # roundness meter
    paste(c, render(FONT, f'"ROND" {rond:>3}', 40, {"ROND": 100, "wght": 700}), 78, 640, ACCENT)
    x0, x1, y = 470, 1520, 672
    c[y - 3 : y + 3, x0:x1] = MUTED * 0.45 + BG * 0.55
    c[y - 3 : y + 3, x0 : int(x0 + (x1 - x0) * rond / 100)] = ACCENT
    cx = int(x0 + (x1 - x0) * rond / 100)
    yy, xx = np.ogrid[:H, :W]
    disk = ((xx - cx) ** 2 + (yy - y) ** 2) <= 15**2
    c[disk] = ACCENT
    return Image.fromarray(c.clip(0, 255).astype(np.uint8))


def main():
    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    frame(100).save(out / "banner.png")
    frames, durations = [], []
    steps = 26
    for i in range(steps + 1):
        t = i / steps
        r = round(100 * (0.5 - 0.5 * math.cos(math.pi * t)))
        frames.append(frame(r))
        durations.append(900 if i in (0, steps) else 45)
    seq = frames + frames[-2:0:-1]
    dur = durations + durations[-2:0:-1]
    small = [f.resize((W // 2, H // 2), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=64) for f in seq]
    small[0].save(out / "morph.gif", save_all=True, append_images=small[1:], duration=dur, loop=0, optimize=True, disposal=2)
    print(out / "banner.png", out / "morph.gif", f"{(out / 'morph.gif').stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
