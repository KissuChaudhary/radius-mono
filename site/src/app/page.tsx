import Compare from "@/components/Compare";
import Faq from "@/components/Faq";
import Features from "@/components/Features";
import Film from "@/components/Film";
import Glyphs from "@/components/Glyphs";
import Hero from "@/components/Hero";
import { DownloadIcon } from "@/components/Icons";
import Install from "@/components/Install";
import Nav from "@/components/Nav";
import Playground from "@/components/Playground";
import { DOWNLOAD, REPO } from "@/lib/site";

export default function Home() {
  return (
    <>
      <Nav />
      <main id="top">
        <div className="hero">
          <Hero />
          <Film />
        </div>
        <Playground />
        <Compare />
        <Features />
        <Glyphs />
        <Install />
        <Faq />
        <section>
          <div className="col">
            <div className="plate final">
              <h2>Round your editor.</h2>
              <p>Free forever under the SIL Open Font License. Eight weights, italics, 153 ligatures and one dial.</p>
              <div className="ctas">
                <a className="btn primary" href={DOWNLOAD} download><DownloadIcon />Download free</a>
                <a className="btn ghost" href={REPO} target="_blank" rel="noopener">Star on GitHub</a>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer>
        <div className="col">
          <div className="row">
            <p>
              Radius Mono is a modified version of JetBrains Mono by Philipp Nurullin and Konstantin Bulenkov, released
              under the SIL Open Font License 1.1. It is not affiliated with or endorsed by JetBrains.
            </p>
            <nav aria-label="Footer">
              <a href={REPO} target="_blank" rel="noopener">GitHub</a>
              <a href={`${REPO}/blob/main/OFL.txt`} target="_blank" rel="noopener">License</a>
              <a href={`${REPO}/blob/main/CHANGELOG.md`} target="_blank" rel="noopener">Changelog</a>
            </nav>
          </div>
        </div>
      </footer>
    </>
  );
}
