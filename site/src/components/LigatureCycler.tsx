"use client";

import { useEffect, useState } from "react";

const LIGS = ["->", "=>", "!==", "<=>", "|>", "::", ">=", "&&", "</>", "~>", "===", "<!--"];

export default function LigatureCycler() {
  const [i, setI] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let t: ReturnType<typeof setTimeout>;
    const id = setInterval(() => {
      setVisible(false);
      t = setTimeout(() => {
        setI((n) => (n + 1) % LIGS.length);
        setVisible(true);
      }, 240);
    }, 1400);
    return () => {
      clearInterval(id);
      clearTimeout(t);
    };
  }, []);

  return (
    <div className="d-lig" aria-hidden="true" style={{ opacity: visible ? 1 : 0 }}>
      {LIGS[i]}
    </div>
  );
}
