import type { ReactNode } from "react";

const FAQ: [string, ReactNode][] = [
  [
    "Is it free for commercial use?",
    <>Yes. Radius Mono is licensed under the SIL Open Font License 1.1. Use it in apps, products, websites, videos and client work. The one thing you can’t do is sell the font files on their own.</>,
  ],
  [
    "How is it different from JetBrains Mono?",
    <>The design, metrics, ligatures and OpenType features are the same. Radius Mono adds a Roundness axis (<code>ROND</code>). At 0 it matches JetBrains Mono; at 100 every visible corner is fully rounded. The default is 100.</>,
  ],
  [
    "Which apps let me change the roundness?",
    <>Any app that exposes variable font axes: VS Code (<code>editor.fontVariations</code>), Ghostty (<code>font-variation</code>), Figma and every modern browser through CSS. Other apps use the default, which is fully round, or you can install the static fonts.</>,
  ],
  [
    "How visible is the rounding at 13 or 14 px?",
    <>Subtle. At small sizes it reads as softer, friendlier text rather than visibly round corners. It shows most at heavier weights and larger sizes: headings, slides, terminals with big type.</>,
  ],
  [
    "Can I turn ligatures off?",
    <>Yes. In VS Code set <code>&quot;editor.fontLigatures&quot;: false</code>. In CSS use <code>font-variant-ligatures: none</code>. Most editors have a similar toggle.</>,
  ],
  ["Does it include Nerd Font icons?", <>Not yet. Patched Nerd Font builds are the next release.</>],
  [
    "Why do box-drawing characters stay sharp?",
    <>Box drawing, block elements and powerline glyphs have to tile into continuous lines in terminals. Rounding them would leave gaps, so they keep their original shapes.</>,
  ],
];

export default function Faq() {
  return (
    <section id="faq">
      <div className="col">
        <div className="head center">
          <div className="eyebrow">FAQ</div>
          <h2>Questions, answered.</h2>
        </div>
        <div className="faq">
          {FAQ.map(([q, a], i) => (
            <details key={q} open={i === 0}>
              <summary>{q}<i aria-hidden="true">+</i></summary>
              <div className="a">{a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
