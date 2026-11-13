"""Cached, shaped text rendering (HarfBuzz + FreeType) to float alpha masks."""
from functools import lru_cache

import freetype
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont


class Face:
    def __init__(self, path):
        self.path = path
        self.blob = hb.Blob.from_file_path(path)
        self.hbface = hb.Face(self.blob)
        self.upem = self.hbface.upem
        self.ft = freetype.Face(path)
        tt = TTFont(path)
        self.axes = [(a.axisTag, a.defaultValue) for a in tt["fvar"].axes] if "fvar" in tt else []
        self._cache = {}

    def mask(self, text, size, rond=100.0, wght=400.0, features=None):
        key = (text, round(size, 1), round(rond, 1), round(wght, 1), tuple(sorted((features or {}).items())))
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        coords = {"ROND": rond, "wght": wght}
        font = hb.Font(self.hbface)
        font.set_variations(coords)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features or {"calt": True, "liga": True})
        ft = self.ft
        ft.set_char_size(int(size * 64))
        if self.axes:
            ft.set_var_design_coords([coords.get(t, d) for t, d in self.axes])
        scale = size / self.upem
        asc = int(round(ft.size.ascender / 64))
        desc = int(round(-ft.size.descender / 64))
        h = asc + desc + 4
        x = 0.0
        parts = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_TARGET_LIGHT)
            g = ft.glyph
            bm = g.bitmap
            if bm.width:
                arr = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.width)
                parts.append((x + pos.x_offset * scale + g.bitmap_left, asc - pos.y_offset * scale - g.bitmap_top, arr))
            x += pos.x_advance * scale
        W = int(np.ceil(x)) + 4
        img = np.zeros((h, W), np.float32)
        for px, py, arr in parts:
            px, py = int(round(px)), int(round(py))
            r, c = arr.shape
            y0, x0, y1, x1 = max(0, py), max(0, px), min(h, py + r), min(W, px + c)
            if y1 > y0 and x1 > x0:
                img[y0:y1, x0:x1] = np.maximum(img[y0:y1, x0:x1], arr[y0 - py : y1 - py, x0 - px : x1 - px] / 255.0)
        res = (img, asc, x)
        if len(self._cache) > 4000:
            self._cache.clear()
        self._cache[key] = res
        return res


def composite(canvas, mask, x, y, color, alpha=1.0, clip=None):
    """Alpha-composite a mask onto an HxWx3 float canvas. clip=(x0, x1) limits columns."""
    H, W = canvas.shape[:2]
    h, w = mask.shape
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    dx1, dy1 = min(W, x + w), min(H, y + h)
    if clip is not None:
        dx0, dx1 = max(dx0, int(clip[0])), min(dx1, int(clip[1]))
        sx0 = dx0 - x
    if dx1 <= dx0 or dy1 <= dy0:
        return
    m = mask[sy0 : sy0 + (dy1 - dy0), sx0 : sx0 + (dx1 - dx0), None] * alpha
    region = canvas[dy0:dy1, dx0:dx1]
    region *= 1 - m
    region += np.asarray(color, np.float32) * m
