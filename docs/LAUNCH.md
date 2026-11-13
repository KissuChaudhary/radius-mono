# Launch kit

## Positioning

**Radius Mono: JetBrains Mono, with a border-radius.**

Three proof points to repeat everywhere:

1. One slider: `ROND` goes from 0 (JetBrains Mono, exactly) to 100 (fully rounded), at every weight.
2. Nothing else changes: same metrics, all 153 ligatures, every OpenType feature. Switching never reflows code.
3. Works in your editor today: `"editor.fontVariations": "'ROND' 60"` in VS Code, `font-variation = ROND=60` in Ghostty.

## Links

- Website: https://kissuchaudhary.github.io/radius-mono/
- Repo: https://github.com/KissuChaudhary/radius-mono
- Download: https://github.com/KissuChaudhary/radius-mono/releases/latest

## Assets

| Asset | File | Use |
|---|---|---|
| Launch film, 16 s, 1080p, with sound | `media/radius-mono-launch.mp4` | X / Bluesky / LinkedIn post, Show HN |
| Morph loop (sharp ↔ round) | `docs/morph.gif` | README hero, replies |
| Static banner 1600×840 | `docs/banner.png` | GitHub social preview |
| OG card 1200×630 | `site/public/og.png` | Link previews (already wired into the site) |
| Stills | `media/frame-parade.jpg`, `media/frame-code.jpg` | Thread images |

Regenerate the film with `python tools/video.py` after any font change.

## Post (X / Bluesky / Threads)

> I gave JetBrains Mono a border-radius.
>
> Radius Mono: one variable font, a ROND axis from 0 (sharp) to 100 (fully round), weights 100–800, upright + italic. All 153 ligatures kept.
>
> Set your editor's roundness: "editor.fontVariations": "'ROND' 60"
>
> Free, OFL. kissuchaudhary.github.io/radius-mono

Attach `media/radius-mono-launch.mp4`. Reply thread:

1. GIF of the before/after drag from the site: "ROND 0 is JetBrains Mono to within 0.07% of the em. Metrics are identical, so nothing reflows."
2. `media/frame-code.jpg`: "Corners hidden inside overlapping strokes stay sharp, so junctions never notch. Ligature joins at cell edges stay sharp, so `->` and `__init__` still connect."
3. "Built on JetBrains Mono by Philipp Nurullin and Konstantin Bulenkov. The rounding engine is MIT, so you can add a roundness axis to other variable fonts too."

## Show HN

Title: `Show HN: Radius Mono – JetBrains Mono with a roundness axis (0–100)`

First comment: what it is, how the engine works (4 steps from the README), what the QA measured, what is next (Nerd Font builds, NL builds).

## Before posting

- [x] Repo created and pushed; repo URL in the fonts' name table.
- [ ] Set `docs/banner.png` as the repository social preview (Settings → General → Social preview).
- [ ] Add topics: `font`, `monospace`, `variable-font`, `coding-font`, `jetbrains-mono`, `ligatures`.
- [ ] Put the website URL in the repo's About box.
- [ ] Have Nerd Font builds ready within a day or two: the first question from terminal users will be about icons.
