"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DOWNLOAD, ZIP_SIZE } from "@/lib/site";
import { DownloadIcon } from "./Icons";
import Range from "./Range";

const PRESETS = [0, 50, 100];
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export default function Hero() {
  const [rond, setRond] = useState(100);
  const raf = useRef(0);
  const cur = useRef(100);

  const apply = useCallback((v: number) => {
    cur.current = v;
    setRond(v);
    document.documentElement.style.setProperty("--rond", String(v));
  }, []);

  const animateTo = useCallback(
    (to: number, dur: number, delay = 0, from?: number) => {
      cancelAnimationFrame(raf.current);
      const start = from ?? cur.current;
      const t0 = performance.now() + delay;
      const tick = (now: number) => {
        const t = Math.min(1, Math.max(0, (now - t0) / dur));
        apply(Math.round(start + (to - start) * ease(t)));
        if (t < 1) raf.current = requestAnimationFrame(tick);
      };
      raf.current = requestAnimationFrame(tick);
    },
    [apply],
  );

  // One orchestrated moment: the layout script started the page sharp; round it now.
  useEffect(() => {
    if (document.documentElement.dataset.intro === "1") {
      setRond(0);
      animateTo(100, 1800, 450, 0);
    }
    return () => cancelAnimationFrame(raf.current);
  }, [animateTo]);

  return (
    <div className="col">
      <a className="pill" href="#install"><b>v1.0</b>Free and open source, SIL OFL 1.1</a>
      <h1>Code with a <span className="soft">border-radius</span>.</h1>
      <p className="sub">
        Radius Mono is JetBrains Mono with one new dial: roundness. Turn it from crisp to fully round, at any weight,
        without moving a single character.
      </p>
      <div className="ctas">
        <a className="btn primary" href={DOWNLOAD} download><DownloadIcon />Download free</a>
        <a className="btn ghost" href="#playground">Try it live</a>
      </div>
      <ul className="trust" aria-label="What you get">
        <li>{ZIP_SIZE} zip</li>
        <li>8 weights + italics</li>
        <li>153 ligatures</li>
        <li>TTF + WOFF2</li>
      </ul>
      <div>
        <div className="dial" role="group" aria-label="Roundness of this page">
          <label htmlFor="rond">Roundness</label>
          <Range id="rond" min={0} max={100} value={rond} onChange={(v) => { cancelAnimationFrame(raf.current); apply(v); }} />
          <output htmlFor="rond">{rond}</output>
          <div className="presets">
            {PRESETS.map((v) => (
              <button key={v} type="button" aria-pressed={rond === v} onClick={() => animateTo(v, 700)}>{v}</button>
            ))}
          </div>
        </div>
        <span className="dial-hint">This dial rounds every letter on this page.</span>
      </div>
    </div>
  );
}
