"use client";

import { useEffect, useState, type CSSProperties } from "react";
import Range from "./Range";

const SAMPLE = "Sphinx of black quartz, judge my vow. const r = (x) => x ?? 0; // != === <= -> {0O 1lI}";

export default function Playground() {
  const [rond, setRond] = useState(100);
  const [wght, setWght] = useState(500);
  const [size, setSize] = useState(64);
  const [italic, setItalic] = useState(false);
  const [ligs, setLigs] = useState(true);

  useEffect(() => {
    if (window.innerWidth < 760) setSize(40);
  }, []);

  const style: CSSProperties = {
    fontSize: size,
    fontStyle: italic ? "italic" : "normal",
    fontVariantLigatures: ligs ? "normal" : "none",
    fontVariationSettings: `"ROND" ${rond}, "wght" ${wght}`,
  };

  return (
    <section id="playground">
      <div className="col">
        <div className="head">
          <div className="eyebrow">Playground</div>
          <h2>Type anything. Then turn the dial.</h2>
          <p className="lede">
            The text below is editable. Every control maps to a real axis or OpenType feature, so what you see is exactly
            what your editor will render.
          </p>
        </div>
        <div className="plate">
          <div className="pg-bar">
            <div className="ctl"><label htmlFor="pgr">Roundness</label><Range id="pgr" min={0} max={100} value={rond} onChange={setRond} /><output>{rond}</output></div>
            <div className="ctl"><label htmlFor="pgw">Weight</label><Range id="pgw" min={100} max={800} value={wght} onChange={setWght} /><output>{wght}</output></div>
            <div className="ctl"><label htmlFor="pgs">Size</label><Range id="pgs" min={16} max={140} value={size} onChange={setSize} /><output>{size}</output></div>
            <div className="seg" role="group" aria-label="Style">
              <button type="button" aria-pressed={!italic} onClick={() => setItalic(false)}>Upright</button>
              <button type="button" aria-pressed={italic} onClick={() => setItalic(true)}>Italic</button>
            </div>
            <div className="seg" role="group" aria-label="Ligatures">
              <button type="button" aria-pressed={ligs} onClick={() => setLigs(true)}>Ligatures</button>
              <button type="button" aria-pressed={!ligs} onClick={() => setLigs(false)}>Off</button>
            </div>
          </div>
          <div
            className="pg-text"
            style={style}
            contentEditable
            suppressContentEditableWarning
            spellCheck={false}
            aria-label="Editable sample text"
          >
            {SAMPLE}
          </div>
          <div className="pg-foot">
            <span>CSS: <code>font-variation-settings: &quot;ROND&quot; {rond}, &quot;wght&quot; {wght};</code></span>
            <span>Click the text to edit</span>
          </div>
        </div>
      </div>
    </section>
  );
}
