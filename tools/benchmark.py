import sys
sys.path.insert(0, "tools")
from render import render_line, axes
import numpy as np
from PIL import Image, ImageDraw, ImageFont
C = "upstream/competitors/"
fonts = [
  ("Inter (sharp source)", "upstream/inter-4.1/extracted/InterVariable.ttf", {}),
  ("Open Runde", C+"OpenRunde-{w}.otf", None),
  ("Intern", C+"Intern.ttf", {}),
  ("Pollen", C+"Pollen.ttf", {"ROND":100}),
  ("Google Sans Flex ROND100", C+"GoogleSansFlex.ttf", {"ROND":100}),
  ("Goeist (Geist)", C+"Goeist.ttf", {}),
  ("OURS (wip) ROND100", "build/test.ttf", {"ROND":100}),
]
text = sys.argv[1]; size = int(sys.argv[2]); wght = int(sys.argv[3]); out = sys.argv[4]
rows = []
for label, path, co in fonts:
    if co is None:
        path = path.format(w="Bold" if wght >= 600 else "Regular"); coords = {}; order = []
    else:
        coords = dict(co); coords["wght"] = wght; order = axes(path)
        if any(t == "opsz" for t, _ in order): coords.setdefault("opsz", 14 if "Flex" not in label else 18)
    rows.append((label, render_line(path, text, size, coords, order)))
W = max(r.shape[1] for _, r in rows) + 330; H = sum(r.shape[0] + 10 for _, r in rows) + 10
canvas = Image.new("L", (W, H), 255); d = ImageDraw.Draw(canvas)
try: lf = ImageFont.truetype("arial.ttf", 22)
except Exception: lf = None
y = 5
for label, r in rows:
    im = Image.fromarray((255 - r * 238).astype(np.uint8)); canvas.paste(im, (320, y))
    d.text((10, y + r.shape[0] // 2 - 12), label, fill=0 if "OURS" in label else 110, font=lf); y += r.shape[0] + 10
canvas.save(out); print(out, canvas.size)
