import sys
from collections import Counter
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1])
print("tables:", sorted(f.keys()))
print("glyphs:", len(f.getGlyphOrder()), "upm", f['head'].unitsPerEm)
for a in f['fvar'].axes:
    print("axis", a.axisTag, a.minValue, a.defaultValue, a.maxValue)
print("instances", [(f['name'].getDebugName(i.subfamilyNameID), i.coordinates) for i in f['fvar'].instances][:30])
if 'avar' in f: print("avar", {k: v for k, v in f['avar'].segments.items()})
peaks = Counter()
glyf = f['glyf']; gvar = f['gvar']
for g, tvs in gvar.variations.items():
    for tv in tvs:
        peaks[tuple(sorted((k, v) for k, v in tv.axes.items()))] += 1
for k, v in peaks.most_common(40): print(v, k)
comp = Counter(); pm = 0; simple = 0
for gn in f.getGlyphOrder():
    g = glyf[gn]
    if g.isComposite():
        comp['composite'] += 1
        for c in g.components:
            if not (c.flags & 0x0002): pm += 1
    elif g.numberOfContours > 0: simple += 1
print("simple", simple, comp, "point-matched components", pm)
print("hinting:", [t for t in ('fpgm','prep','cvt ','cvar','gasp') if t in f])
print("name:", f['name'].getDebugName(1), "|", f['name'].getDebugName(4), "|", f['name'].getDebugName(5))
print("OS2 weight", f['OS/2'].usWeightClass, "vendor", f['OS/2'].achVendID)
print("GSUB features:", sorted({fr.FeatureTag for fr in f['GSUB'].table.FeatureList.FeatureRecord}))
ovl = sum(1 for gn in f.getGlyphOrder() if glyf[gn].numberOfContours > 0 and glyf[gn].flags and (glyf[gn].flags[0] & 0x40))
print("glyphs w/ OVERLAP_SIMPLE flag:", ovl)
