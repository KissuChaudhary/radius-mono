import LigatureCycler from "./LigatureCycler";

export default function Features() {
  return (
    <section id="features">
      <div className="col">
        <div className="head">
          <div className="eyebrow">Features</div>
          <h2>Everything JetBrains Mono does. Plus a dial.</h2>
        </div>
        <div className="bento">
          <article className="plate tile wide">
            <div className="demo">
              <div className="d-rond" aria-hidden="true"><span className="ghost">a</span><span className="live">a</span></div>
            </div>
            <div className="txt">
              <h3>Roundness, 0 to 100</h3>
              <p>A continuous axis. Pick 30 for a hint of softness or 100 for fully round terminals. The orange is the sharp outline peeking out underneath.</p>
            </div>
          </article>
          <article className="plate tile">
            <div className="demo"><div className="d-wght" aria-hidden="true">Aa</div></div>
            <div className="txt"><h3>Eight weights</h3><p>Thin to ExtraBold, and every value in between.</p></div>
          </article>
          <article className="plate tile">
            <div className="demo"><LigatureCycler /></div>
            <div className="txt"><h3>153 code ligatures</h3><p>Arrows, comparisons and operators, rounded too.</p></div>
          </article>
          <article className="plate tile">
            <div className="demo">
              <div className="d-join" aria-hidden="true"><span>__init__</span><span>---&gt;</span><span>====</span></div>
            </div>
            <div className="txt"><h3>Seamless joins</h3><p>Where ligature pieces meet the next cell, corners stay sharp, so runs connect.</p></div>
          </article>
          <article className="plate tile">
            <div className="demo"><div className="d-ital" aria-hidden="true">Italic</div></div>
            <div className="txt"><h3>True italics</h3><p>The italic is rounded corner for corner, in all eight weights.</p></div>
          </article>
          <article className="plate tile wide">
            <div className="demo">
              <div className="d-reflow" aria-hidden="true">
                <div>if (user?.isAdmin) return render(dashboard);<small>ROND 0</small></div>
                <div>if (user?.isAdmin) return render(dashboard);<small>ROND 100</small></div>
              </div>
            </div>
            <div className="txt"><h3>Zero reflow</h3><p>Advance widths and metrics are untouched. Every line breaks exactly where it did in JetBrains Mono.</p></div>
          </article>
          <article className="plate tile">
            <div className="demo">
              <div className="d-lang" aria-hidden="true"><span>Ж</span><span>λ</span><span>ß</span><span>Ω</span></div>
            </div>
            <div className="txt"><h3>Latin, Cyrillic, Greek</h3><p>1,363 characters, with box drawing and powerline symbols that still tile.</p></div>
          </article>
        </div>
      </div>
    </section>
  );
}
