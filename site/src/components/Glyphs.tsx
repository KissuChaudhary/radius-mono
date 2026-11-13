"use client";

import { useState } from "react";
import glyphs from "@/data/glyphs.json";

type Glyph = [char: string, name: string, codepoint: string];
const LIST = glyphs as Glyph[];
const START = Math.max(0, LIST.findIndex(([c]) => c === "R"));

export default function Glyphs() {
  const [sel, setSel] = useState(START);
  const [ch, name, cp] = LIST[sel];

  return (
    <section id="glyphs">
      <div className="col">
        <div className="head">
          <div className="eyebrow">Character set</div>
          <h2>Look closer.</h2>
          <p className="lede">Pick any character. The preview follows the Roundness dial at the top of the page.</p>
        </div>
        <div className="glyphs">
          <div className="grid" role="group" aria-label="Characters">
            {LIST.map(([c, n], i) => (
              <button
                key={c}
                type="button"
                aria-label={n}
                aria-pressed={i === sel}
                onClick={() => setSel(i)}
                onPointerEnter={(e) => e.pointerType === "mouse" && setSel(i)}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="plate preview" aria-live="polite">
            <div className="stage">
              <span className="ghost" aria-hidden="true">{ch}</span>
              <span className="live">{ch}</span>
            </div>
            <div className="meta"><span>{name}</span><b>{cp}</b></div>
          </div>
        </div>
      </div>
    </section>
  );
}
