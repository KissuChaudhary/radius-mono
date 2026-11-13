"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import { DOWNLOAD, ZIP_NAME, ZIP_SIZE } from "@/lib/site";

const TABS = [
  {
    id: "vscode",
    label: "VS Code",
    code: `// settings.json
{
  "editor.fontFamily": "Radius Mono",
  "editor.fontLigatures": true,
  "editor.fontVariations": "'ROND' 100, 'wght' 400"
}`,
  },
  {
    id: "jetbrains",
    label: "JetBrains IDEs",
    code: `Settings → Editor → Font
  Font:              Radius Mono
  Enable ligatures:  on

Settings → Editor → Color Scheme → Console Font
  Use console font instead of the default:  on
  Font:              Radius Mono`,
  },
  {
    id: "ghostty",
    label: "Ghostty",
    code: `# ~/.config/ghostty/config
font-family = Radius Mono
font-variation = ROND=100
font-variation = wght=400`,
  },
  {
    id: "zed",
    label: "Zed",
    code: `// settings.json
{
  "buffer_font_family": "Radius Mono",
  "buffer_font_features": { "calt": true }
}`,
  },
  {
    id: "web",
    label: "Web",
    code: `@font-face {
  font-family: "Radius Mono";
  src: url("RadiusMono[ROND,wght].woff2") format("woff2");
  font-weight: 100 800;
  font-display: swap;
}

code, pre {
  font-family: "Radius Mono", ui-monospace, monospace;
  font-variation-settings: "ROND" 100;
}`,
  },
];

export default function Install() {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState<"idle" | "done" | "select">("idle");
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const preRef = useRef<HTMLPreElement>(null);

  const onKey = (e: KeyboardEvent, i: number) => {
    const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!d) return;
    const n = (i + d + TABS.length) % TABS.length;
    setActive(n);
    tabRefs.current[n]?.focus();
  };

  const copy = () => {
    const text = TABS[active].code;
    const fallback = () => {
      const pre = preRef.current;
      if (pre) {
        const r = document.createRange();
        r.selectNodeContents(pre);
        const s = window.getSelection();
        s?.removeAllRanges();
        s?.addRange(r);
      }
      setCopied("select");
    };
    try {
      navigator.clipboard.writeText(text).then(() => {
        setCopied("done");
        setTimeout(() => setCopied("idle"), 1500);
      }, fallback);
    } catch {
      fallback();
    }
  };

  return (
    <section id="install">
      <div className="col">
        <div className="head">
          <div className="eyebrow">Install</div>
          <h2>Ready in a minute.</h2>
        </div>
        <div className="steps">
          <div className="plate step">
            <span className="num">1</span>
            <h3>Download</h3>
            <p>One zip with the variable fonts, 16 static fonts and webfonts.</p>
            <div><a className="btn primary sm" href={DOWNLOAD} download>Download Radius Mono</a></div>
            <span className="files">{ZIP_NAME} · {ZIP_SIZE}</span>
          </div>
          <div className="plate step">
            <span className="num">2</span>
            <h3>Install the fonts</h3>
            <ul>
              <li><b>macOS</b> Open the .ttf files and click Install.</li>
              <li><b>Windows</b> Select them, right-click, Install for all users.</li>
              <li><b>Linux</b> Copy to <code>~/.local/share/fonts</code>, then run <code>fc-cache -f</code>.</li>
            </ul>
            <p>Use <code>variable/</code> to pick any roundness. Use <code>ttf/</code> in apps without axis controls; those are fully round.</p>
          </div>
          <div className="plate step">
            <span className="num">3</span>
            <h3>Pick it in your editor</h3>
            <p>Set the family to <code>Radius Mono</code>. In VS Code, Ghostty and on the web you can also choose the roundness.</p>
            <p>Settings for each editor are below.</p>
          </div>
        </div>
        <div className="plate tabs">
          <div className="tablist" role="tablist" aria-label="Editor settings">
            {TABS.map((t, i) => (
              <button
                key={t.id}
                ref={(el) => { tabRefs.current[i] = el; }}
                role="tab"
                id={`tab-${t.id}`}
                aria-selected={i === active}
                aria-controls={`panel-${t.id}`}
                tabIndex={i === active ? 0 : -1}
                onClick={() => setActive(i)}
                onKeyDown={(e) => onKey(e, i)}
              >
                {t.label}
              </button>
            ))}
            <button type="button" className={`copy${copied === "done" ? " done" : ""}`} onClick={copy}>
              {copied === "done" ? "Copied" : copied === "select" ? "Press Ctrl+C" : "Copy"}
            </button>
          </div>
          {TABS.map((t, i) => (
            <div key={t.id} className="panel" role="tabpanel" id={`panel-${t.id}`} aria-labelledby={`tab-${t.id}`} hidden={i !== active}>
              <pre ref={i === active ? preRef : undefined}>{t.code}</pre>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
