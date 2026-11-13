"""Shaped (HarfBuzz) + FreeType render of lines -> PNG. Usage: font out --size N --line 'text|AXIS=v,...'"""
import argparse
import freetype, numpy as np, uharfbuzz as hb
from PIL import Image
from fontTools.ttLib import TTFont

def render(path, text, size, coords, features=None):
    blob = hb.Blob.from_file_path(path); face = hb.Face(blob); font = hb.Font(face)
    upem = face.upem
    if coords: font.set_variations(coords)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, features or {"calt": True, "liga": True})
    ft = freetype.Face(path); ft.set_char_size(size * 64)
    order = [a.axisTag for a in TTFont(path)['fvar'].axes] if 'fvar' in TTFont(path) else []
    if order: ft.set_var_design_coords([coords.get(t, d) for t, d in [(a.axisTag, a.defaultValue) for a in TTFont(path)['fvar'].axes]])
    scale = size / upem
    asc = int(ft.size.ascender / 64); h = asc + int(-ft.size.descender / 64) + 4
    x = 8.0; parts = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = ft.glyph; bm = g.bitmap
        if bm.width:
            arr = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)
            parts.append((x + pos.x_offset * scale + g.bitmap_left, asc - pos.y_offset * scale - g.bitmap_top, arr))
        x += pos.x_advance * scale
    W = int(x) + 16; img = np.zeros((h, W), np.float32)
    for px, py, arr in parts:
        px, py = int(round(px)), int(round(py)); r, c = arr.shape
        y0, x0, y1, x1 = max(0, py), max(0, px), min(h, py + r), min(W, px + c)
        if y1 > y0 and x1 > x0:
            img[y0:y1, x0:x1] = np.maximum(img[y0:y1, x0:x1], arr[y0-py:y1-py, x0-px:x1-px] / 255)
    return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("font"); ap.add_argument("out")
    ap.add_argument("--size", type=int, default=120); ap.add_argument("--line", action="append", required=True)
    a = ap.parse_args(); rows = []
    for spec in a.line:
        t, _, c = spec.rpartition("@@"); co = {k: float(v) for k, v in (kv.split("=") for kv in c.split(",") if kv)}
        rows.append(render(a.font, t, a.size, co))
    W = max(r.shape[1] for r in rows); H = sum(r.shape[0] for r in rows)
    can = np.zeros((H, W), np.float32); y = 0
    for r in rows: can[y:y+r.shape[0], :r.shape[1]] = r; y += r.shape[0]
    Image.fromarray((255 - can * 238).astype(np.uint8)).save(a.out); print(a.out, (W, H))
