"""
Prepare assets for the Next.js site in site/.

    python tools/build_site.py             # everything (needs requirements.txt)
    python tools/build_site.py --zip-only  # just the release zip (stdlib only)

Writes
  site/src/app/fonts/*.woff2      variable webfonts for next/font/local
  site/src/app/icon.svg           favicon (the R, ExtraBold, ROND 100)
  site/src/data/glyphs.json       character-set browser data
  site/src/data/release.json      version + zip name/size shown on the page
  site/public/{og.png,poster.jpg,radius-mono-launch.mp4}
  build/release/RadiusMono-<version>.zip          upload this to the GitHub release
"""
import argparse
import json
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
VERSION = "1.000"
ZIP_NAME = f"RadiusMono-{VERSION}.zip"
UP = ROOT / "fonts" / "webfonts" / "RadiusMono[ROND,wght].woff2"
IT = ROOT / "fonts" / "webfonts" / "RadiusMono-Italic[ROND,wght].woff2"


def human(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n // 1024} KB"


def make_zip():
    out = ROOT / "build" / "release" / ZIP_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for sub in ("variable", "ttf", "webfonts"):
            for p in sorted((ROOT / "fonts" / sub).glob("*")):
                z.write(p, f"RadiusMono-{VERSION}/{sub}/{p.name}")
        for name in ("OFL.txt", "README.md", "CHANGELOG.md"):
            z.write(ROOT / name, f"RadiusMono-{VERSION}/{name}")
    size = human(out.stat().st_size)
    (SITE / "src" / "data").mkdir(parents=True, exist_ok=True)
    (SITE / "src" / "data" / "release.json").write_text(
        json.dumps({"version": VERSION, "zipName": ZIP_NAME, "zipSize": size}, indent=2) + "\n", encoding="utf-8"
    )
    return out, size


def glyph_list():
    from fontTools.ttLib import TTFont

    cmap = TTFont(UP).getBestCmap()
    chars = (
        [chr(c) for c in range(0x41, 0x5B)] + [chr(c) for c in range(0x61, 0x7B)] + [chr(c) for c in range(0x30, 0x3A)]
        + list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
        + list("ßæøœÆØŒðþ€£¥¢©®°±×÷¶§µ←↑→↓↔≠≤≥≈∞")
        + list("ΑΒΓΔΛΣΩαβγδλπσωЖЗИЛФЯжзлфщя")
    )
    out = []
    for ch in chars:
        if ord(ch) in cmap:
            name = unicodedata.name(ch, "").title().replace("Latin ", "").replace("Letter ", "") or "Character"
            out.append([ch, name, f"U+{ord(ch):04X}"])
    return out


def favicon_svg(out):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    st = instancer.instantiateVariableFont(TTFont(ROOT / "fonts" / "variable" / "RadiusMono[ROND,wght].ttf"), {"wght": 800, "ROND": 100}, inplace=False)
    gs = st.getGlyphSet()
    g = st["glyf"]["R"]
    g.recalcBounds(st["glyf"])
    w, h = g.xMax - g.xMin, g.yMax - g.yMin
    s = 38 / max(w, h)
    pen = SVGPathPen(gs)
    gs["R"].draw(TransformPen(pen, (s, 0, 0, -s, 32 - (g.xMin + w / 2) * s, 32 + (g.yMin + h / 2) * s)))
    out.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#000"/>'
        f'<path fill="#F4F4F5" d="{pen.getCommands()}"/></svg>\n',
        encoding="utf-8",
    )


def og_image(out):
    import numpy as np
    from PIL import Image

    sys.path.insert(0, str(Path(__file__).parent))
    from textrender import Face, composite

    up = Face(str(ROOT / "fonts" / "variable" / "RadiusMono[ROND,wght].ttf"))
    it = Face(str(ROOT / "fonts" / "variable" / "RadiusMono-Italic[ROND,wght].ttf"))
    W, H = 1200, 630
    c = np.zeros((H, W, 3), np.float32)
    composite(c, up.mask("Radius Mono", 132, 100, 800)[0], 72, 120, (244, 244, 245))
    composite(c, it.mask("JetBrains Mono, with a border-radius.", 38, 100, 400)[0], 78, 300, (139, 139, 146))
    composite(c, up.mask("const r = (x) => x ?? 0; // != ===", 32, 100, 600)[0], 78, 392, (207, 207, 211))
    composite(c, up.mask('"ROND" 100', 28, 100, 700)[0], 78, 515, (255, 122, 82))
    x0, x1, y = 300, 1128, 534
    c[y - 2 : y + 2, x0:x1] = (255, 122, 82)
    yy, xx = np.ogrid[:H, :W]
    c[((xx - x1) ** 2 + (yy - y) ** 2) <= 12**2] = (244, 244, 245)
    Image.fromarray(c.clip(0, 255).astype(np.uint8)).save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip-only", action="store_true")
    a = ap.parse_args()
    zpath, size = make_zip()
    print("zip", zpath.relative_to(ROOT), size)
    if a.zip_only:
        return
    fonts = SITE / "src" / "app" / "fonts"
    pub = SITE / "public"
    fonts.mkdir(parents=True, exist_ok=True)
    shutil.copy(UP, fonts / "RadiusMono-Variable.woff2")
    shutil.copy(IT, fonts / "RadiusMono-Italic-Variable.woff2")
    shutil.copy(ROOT / "media" / "radius-mono-launch-web.mp4", pub / "radius-mono-launch.mp4")
    shutil.copy(ROOT / "media" / "poster.jpg", pub / "poster.jpg")
    favicon_svg(SITE / "src" / "app" / "icon.svg")
    og_image(pub / "og.png")
    (SITE / "src" / "data" / "glyphs.json").write_text(json.dumps(glyph_list(), ensure_ascii=False) + "\n", encoding="utf-8")
    print("assets ready")


if __name__ == "__main__":
    main()
