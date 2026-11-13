"use client";

import { useEffect, useState } from "react";
import { DOWNLOAD, REPO, REPO_SLUG } from "@/lib/site";
import { GitHubIcon } from "./Icons";

const LINKS = [
  ["#playground", "Playground"],
  ["#features", "Features"],
  ["#glyphs", "Characters"],
  ["#install", "Install"],
  ["#faq", "FAQ"],
] as const;

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [stars, setStars] = useState<number | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    // Live star count; quietly skipped if the API is unreachable or rate-limited.
    fetch(`https://api.github.com/repos/${REPO_SLUG}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => typeof j?.stargazers_count === "number" && setStars(j.stargazers_count))
      .catch(() => {});
  }, []);

  return (
    <header className={`nav${scrolled ? " scrolled" : ""}`}>
      <div className="col">
        <a className="brand" href="#top" aria-label="Radius Mono home">
          <span className="mark" aria-hidden="true">R</span>
          Radius Mono
          <span className="ver">v1.0</span>
        </a>
        <nav className="links" aria-label="Sections">
          {LINKS.map(([href, label]) => (
            <a key={href} href={href}>{label}</a>
          ))}
        </nav>
        <div className="act">
          <a className="btn ghost sm" href={REPO} target="_blank" rel="noopener">
            <GitHubIcon />
            <span className="gh-label">Star</span>
            {stars !== null && stars >= 10 && <span className="count">{stars.toLocaleString()}</span>}
          </a>
          <a className="btn primary sm" href={DOWNLOAD}>Download</a>
        </div>
      </div>
    </header>
  );
}
