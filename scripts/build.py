"""
Build Radius Mono: JetBrains Mono with a continuous roundness axis.

    python scripts/build.py            # variable + webfonts + statics
    python scripts/build.py --fast     # variable fonts only

Outputs (all under fonts/):
    variable/RadiusMono[ROND,wght].ttf, variable/RadiusMono-Italic[ROND,wght].ttf
    webfonts/*.woff2 + radius-mono.css
    ttf/RadiusMono-<Weight>[Italic].ttf   (ROND=100, overlaps removed)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.varLib.instancer import OverlapMode

sys.path.insert(0, str(Path(__file__).parent))
from roundify import RoundParams, add_roundness_axis  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ configuration
FAMILY = "Radius Mono"
PS_FAMILY = "RadiusMono"
VERSION = "1.000"
VENDOR = "NONE"
REPO_URL = "https://github.com/KissuChaudhary/radius-mono"
YEAR = 2026
COPYRIGHT = (
    f"Copyright {YEAR} The Radius Mono Project Authors ({REPO_URL}). "
    "Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)"
)
MANUFACTURER = "The Radius Mono Project Authors"
DESIGNER = "Radius Mono Project Authors (rounding); Philipp Nurullin, Konstantin Bulenkov (JetBrains Mono)"
DESCRIPTION = (
    "Radius Mono is JetBrains Mono with a continuous Roundness axis (ROND 0-100): "
    "from crisp to fully rounded, at every weight."
)
LICENSE = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"

UPSTREAM = {
    "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
    "sha256": "6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf",
    "dir": ROOT / "upstream" / "jbm-2.304",
    "files": {
        "upright": "fonts/variable/JetBrainsMono[wght].ttf",
        "italic": "fonts/variable/JetBrainsMono-Italic[wght].ttf",
    },
}

WEIGHTS = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}

PARAMS = RoundParams(
    convex=0.5,  # fully rounded terminals at ROND=100 (round pen as wide as the stem)
    concave=0.11,
    smoothing=0.3,  # slight squircle tension, still reads as round
    reach=0.2,
    keep_cell_joins=True,  # ligature pieces / underscores must keep joining
    stem_probe="l",
    stem_probe_height=0.5,
)
ROND_DEFAULT = 100.0


# ------------------------------------------------------------------ upstream
def fetch_upstream() -> dict:
    d = UPSTREAM["dir"]
    paths = {k: d / "extracted" / v for k, v in UPSTREAM["files"].items()}
    if all(p.exists() for p in paths.values()):
        return paths
    print(f"downloading {UPSTREAM['url']}")
    data = urllib.request.urlopen(UPSTREAM["url"]).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != UPSTREAM["sha256"]:
        raise SystemExit(f"checksum mismatch: {digest}")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(d / "extracted")
    return paths


# ------------------------------------------------------------------ naming
def set_name(font, name_id, value):
    font["name"].setName(value, name_id, 3, 1, 0x409)


def rename(font: TTFont, italic: bool):
    name = font["name"]
    style = "Italic" if italic else "Regular"
    ps_style = "Italic" if italic else "Regular"
    # drop upstream identity: trademark, vendor URLs, old unique ids
    for nid in (7, 11, 12, 16, 17, 21, 22):
        name.removeNames(nameID=nid)
    set_name(font, 11, REPO_URL)
    set_name(font, 12, REPO_URL)
    name.names = [r for r in name.names if r.platformID == 3]
    set_name(font, 0, COPYRIGHT)
    set_name(font, 1, FAMILY)
    set_name(font, 2, style)
    set_name(font, 3, f"{VERSION};{VENDOR};{PS_FAMILY}-{ps_style}")
    set_name(font, 4, f"{FAMILY} {style}")
    set_name(font, 5, f"Version {VERSION}")
    set_name(font, 6, f"{PS_FAMILY}-{ps_style}")
    set_name(font, 8, MANUFACTURER)
    set_name(font, 9, DESIGNER)
    set_name(font, 10, DESCRIPTION)
    set_name(font, 13, LICENSE)
    set_name(font, 14, LICENSE_URL)
    set_name(font, 25, PS_FAMILY + ("Italic" if italic else ""))
    font["head"].fontRevision = float(VERSION)
    font["OS/2"].achVendID = VENDOR


def build_stat(font: TTFont, italic: bool):
    wght_values = []
    for v, n in WEIGHTS.items():
        rec = {"value": v, "name": n}
        if v == 400:
            rec.update(flags=0x2, linkedValue=700)
        wght_values.append(rec)
    axes = [
        {"tag": "wght", "name": "Weight", "values": wght_values},
        {
            "tag": "ROND",
            "name": "Roundness",
            "values": [
                {"value": 0, "name": "Sharp"},
                {"value": 50, "name": "Soft"},
                {"value": 100, "name": "Round", "flags": 0x2},
            ],
        },
        {
            "tag": "ital",
            "name": "Italic",
            "values": [{"value": 1, "name": "Italic"}]
            if italic
            else [{"value": 0, "name": "Roman", "flags": 0x2, "linkedValue": 1}],
        },
    ]
    buildStatTable(font, axes, elidedFallbackName="Regular")


def name_instances(font: TTFont, italic: bool):
    name = font["name"]
    for inst in font["fvar"].instances:
        w = int(inst.coordinates["wght"])
        wname = WEIGHTS[w]
        sub = (f"{wname} Italic" if wname != "Regular" else "Italic") if italic else wname
        inst.subfamilyNameID = name.addName(sub, platforms=((3, 1, 0x409),), minNameID=256)
        inst.postscriptNameID = name.addName(
            f"{PS_FAMILY}-{sub.replace(' ', '')}", platforms=((3, 1, 0x409),), minNameID=256
        )


# ------------------------------------------------------------------ statics
def make_static(vf: TTFont, weight: int, italic: bool) -> TTFont:
    st = instancer.instantiateVariableFont(
        vf, {"wght": weight, "ROND": ROND_DEFAULT}, inplace=False, overlap=OverlapMode.REMOVE
    )
    wname = WEIGHTS[weight]
    ribbi = wname in ("Regular", "Bold")
    if ribbi:
        fam = FAMILY
        sub = ("Bold " if wname == "Bold" else "") + ("Italic" if italic else "")
        sub = sub.strip() or "Regular"
    else:
        fam = f"{FAMILY} {wname}"
        sub = "Italic" if italic else "Regular"
    full_style = (f"{wname} Italic" if wname != "Regular" else "Italic") if italic else wname
    ps = f"{PS_FAMILY}-{full_style.replace(' ', '')}"
    name = st["name"]
    for nid in (16, 17, 25):
        name.removeNames(nameID=nid)
    set_name(st, 1, fam)
    set_name(st, 2, sub)
    set_name(st, 3, f"{VERSION};{VENDOR};{ps}")
    set_name(st, 4, f"{FAMILY} {full_style}")
    set_name(st, 6, ps)
    if not ribbi:
        set_name(st, 16, FAMILY)
        set_name(st, 17, full_style)
    os2 = st["OS/2"]
    os2.usWeightClass = weight
    sel = os2.fsSelection & ~0b1100001  # clear ITALIC(0), BOLD(5), REGULAR(6)
    if italic:
        sel |= 1
    if wname == "Bold":
        sel |= 1 << 5
    if not italic and wname != "Bold":
        sel |= 1 << 6
    os2.fsSelection = sel
    st["head"].macStyle = (1 if wname == "Bold" else 0) | (2 if italic else 0)
    return st, ps


# ------------------------------------------------------------------ main
def build(fast=False):
    t0 = time.time()
    src = fetch_upstream()
    out_var = ROOT / "fonts" / "variable"
    out_web = ROOT / "fonts" / "webfonts"
    out_ttf = ROOT / "fonts" / "ttf"
    for d in (out_var, out_web, out_ttf):
        d.mkdir(parents=True, exist_ok=True)

    built = {}
    for style, path in src.items():
        italic = style == "italic"
        print(f"[{style}] rounding {path.name}")
        vf = TTFont(path)
        stats = add_roundness_axis(vf, PARAMS, axis_default=ROND_DEFAULT, log=lambda m: print("   ", m))
        print(f"    {stats}")
        rename(vf, italic)
        build_stat(vf, italic)
        name_instances(vf, italic)
        vf["name"].removeUnusedNames(vf)
        fname =f"{PS_FAMILY}{'-Italic' if italic else ''}[ROND,wght]"
        vf.save(out_var / f"{fname}.ttf")
        vf = TTFont(out_var / f"{fname}.ttf")
        built[style] = vf
        web = TTFont(out_var / f"{fname}.ttf")
        web.flavor = "woff2"
        web.save(out_web / f"{fname}.woff2")
        print(f"    -> {fname}.ttf / .woff2  ({time.time() - t0:.0f}s)")

    (out_web / "radius-mono.css").write_text(
        "\n".join(
            f"""@font-face {{
  font-family: "{FAMILY}";
  src: url("{PS_FAMILY}{'-Italic' if it else ''}[ROND,wght].woff2") format("woff2");
  font-weight: 100 800;
  font-style: {'italic' if it else 'normal'};
  font-display: swap;
}}"""
            for it in (False, True)
        )
        + "\n",
        encoding="utf-8",
    )

    if not fast:
        for style, vf in built.items():
            italic = style == "italic"
            for w in WEIGHTS:
                st, ps = make_static(vf, w, italic)
                st.save(out_ttf / f"{ps}.ttf")
            print(f"[{style}] statics done ({time.time() - t0:.0f}s)")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="variable fonts + webfonts only")
    build(**vars(ap.parse_args()))
