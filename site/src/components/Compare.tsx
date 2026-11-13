"use client";

import { useRef, useState, type CSSProperties, type PointerEvent } from "react";
import { CODE } from "@/lib/site";
import { SplitIcon } from "./Icons";
import Range from "./Range";

function Code() {
  return (
    <>
      {CODE.map((line, i) => (
        <span key={i}>
          {line.map(([cls, text], j) => (cls ? <span key={j} className={cls}>{text}</span> : text))}
          {i < CODE.length - 1 ? "\n" : null}
        </span>
      ))}
    </>
  );
}

export default function Compare() {
  const [split, setSplit] = useState(50);
  const [weight, setWeight] = useState(560);
  const box = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const at = (e: PointerEvent) => {
    const el = box.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left + el.scrollLeft;
    setSplit(Math.round(Math.min(100, Math.max(0, (x / el.scrollWidth) * 100))));
  };

  return (
    <section id="compare">
      <div className="col">
        <div className="head">
          <div className="eyebrow">Before / after</div>
          <h2>Same code. Softer corners.</h2>
          <p className="lede">
            Left of the line is ROND 0, which matches JetBrains Mono. Right of it is ROND 100. Widths, spacing and line
            breaks are identical, so switching never reflows a file. Drag across the code.
          </p>
        </div>
        <div className="plate editor">
          <div className="ed-bar">
            <span className="dots"><i /><i /><i /></span>
            <span className="tab">fillet.ts</span>
            <span className="lang">TypeScript</span>
          </div>
          <div
            className="ba"
            ref={box}
            style={{ "--split": `${split}%`, "--cw": weight } as CSSProperties}
            onPointerDown={(e) => { dragging.current = true; e.currentTarget.setPointerCapture(e.pointerId); at(e); }}
            onPointerMove={(e) => dragging.current && at(e)}
            onPointerUp={() => { dragging.current = false; }}
            onPointerCancel={() => { dragging.current = false; }}
          >
            <pre className="rd" aria-hidden="true"><Code /></pre>
            <pre className="sh"><Code /></pre>
            <div className="line" />
            <div className="knob"><SplitIcon /></div>
            <span className="tag l">ROND 0</span>
            <span className="tag r">ROND 100</span>
          </div>
          <div className="cmp-foot">
            <label htmlFor="split">Split</label>
            <Range id="split" min={0} max={100} value={split} onChange={setSplit} />
            <label htmlFor="cw">Weight</label>
            <Range id="cw" min={100} max={800} value={weight} onChange={setWeight} />
          </div>
        </div>
      </div>
    </section>
  );
}
