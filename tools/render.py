"""Render text with a variable font at given axis coords -> PNG (FreeType, grayscale AA)."""
import sys, argparse
import freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont

def render_line(path, text, size, coords, axes_order, fg=(17,17,17)):
    face = freetype.Face(path)
    face.set_char_size(size * 64)
    if coords:
        face.set_var_design_coords([coords.get(t, d) for t, d in axes_order])
    pen_x = 0
    asc = face.size.ascender // 64; desc = -face.size.descender // 64
    h = asc + desc + 4
    glyphs = []
    width = 0
    for ch in text:
        face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bmp = g.bitmap
        arr = np.array(bmp.buffer, dtype=np.uint8).reshape(bmp.rows, bmp.width) if bmp.width else None
        glyphs.append((pen_x + g.bitmap_left, asc - g.bitmap_top, arr))
        pen_x += g.advance.x / 64
    W = int(pen_x) + 8
    img = np.zeros((h, W), dtype=np.float32)
    for x, y, arr in glyphs:
        if arr is None: continue
        x = int(round(x)); r, c = arr.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(h, y + r), min(W, x + c)
        img[y0:y1, x0:x1] = np.maximum(img[y0:y1, x0:x1], arr[y0-y:y1-y, x0-x:x1-x] / 255.0)
    return img

def axes(path):
    face = freetype.Face(path)
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    return [(a.axisTag, a.defaultValue) for a in f['fvar'].axes]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("font"); ap.add_argument("out")
    ap.add_argument("--size", type=int, default=160)
    ap.add_argument("--line", action="append", required=True, help="text|ROND=100,wght=400")
    ap.add_argument("--label", action="store_true")
    a = ap.parse_args()
    order = axes(a.font)
    rows = []
    for spec in a.line:
        text, _, c = spec.partition("|")
        coords = {k: float(v) for k, v in (kv.split("=") for kv in c.split(",") if kv)}
        img = render_line(a.font, text, a.size, coords, order)
        rows.append((img, c))
    W = max(r.shape[1] for r, _ in rows) + 20
    H = sum(r.shape[0] + 6 for r, _ in rows) + 10
    canvas = np.zeros((H, W), dtype=np.float32)
    y = 5
    for r, c in rows:
        canvas[y:y+r.shape[0], 10:10+r.shape[1]] = r
        y += r.shape[0] + 6
    out = Image.fromarray((255 - canvas * 238).astype(np.uint8))
    if a.label:
        d = ImageDraw.Draw(out); y = 5
        for r, c in rows:
            d.text((W - 260, y + 4), c, fill=120); y += r.shape[0] + 6
    out.save(a.out)
    print(a.out, out.size)
