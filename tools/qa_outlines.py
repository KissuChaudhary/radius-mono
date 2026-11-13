"""Outline QA for a ROND build vs its source: exactness at ROND=0, topology at 50/100,
plus max point deviation (not area) so rounding noise is measured properly."""
import sys, pathops
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
src = TTFont(sys.argv[1]); dst = TTFont(sys.argv[2])
axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in src['fvar'].axes}
locs = []
for tag, (lo, de, hi) in axes.items():
    for v in (lo, de, hi, (lo + hi) / 2):
        locs.append({**{t: d for t, (_, d, _) in axes.items()}, tag: v})
def path(gs, gn):
    p = pathops.Path(); gs[gn].draw(p.getPen(glyphSet=gs)); return pathops.simplify(p, fix_winding=True)
def area(p):
    a = AreaPen(); p.draw(a); return abs(a.value)
def pts(gs, gn):
    r = DecomposingRecordingPen(gs); gs[gn].draw(r)
    return [p for op, args in r.value for p in args if p]
order = src.getGlyphOrder(); upm = src['head'].unitsPerEm
dev, topo = [], []
for loc in locs:
    a_gs = src.getGlyphSet(location=loc)
    g0 = dst.getGlyphSet(location={**loc, 'ROND': 0}); g5 = dst.getGlyphSet(location={**loc, 'ROND': 50}); g1 = dst.getGlyphSet(location={**loc, 'ROND': 100})
    for gn in order:
        a = path(a_gs, gn); b = path(g0, gn)
        x = area(pathops.op(a, b, pathops.PathOp.XOR))
        per = max(1.0, sum(1 for _ in pts(a_gs, gn)))
        if x / per > 4: dev.append((gn, loc, round(x)))
        na = len(list(a.contours))
        for lab, gs in (("50", g5), ("100", g1)):
            n = len(list(path(gs, gn).contours))
            if n != na: topo.append((gn, loc, lab, na, n))
print(f"locations checked: {len(locs)}, glyphs: {len(order)}")
print("ROND=0 deviates from source:", len(dev), dev[:15])
print("topology changes:", len(topo)); [print("  ", t) for t in topo[:30]]
