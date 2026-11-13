"use client";

import { useEffect, useRef, useState } from "react";
import { asset } from "@/lib/site";
import { SoundIcon } from "./Icons";

export default function Film() {
  const ref = useRef<HTMLVideoElement>(null);
  const [sound, setSound] = useState(false);

  // Play only while on screen; never autoplay for reduced-motion users.
  useEffect(() => {
    const v = ref.current;
    if (!v || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const io = new IntersectionObserver(
      ([e]) => (e.isIntersecting ? v.play().catch(() => {}) : v.pause()),
      { threshold: 0.35 },
    );
    io.observe(v);
    return () => io.disconnect();
  }, []);

  const toggle = () => {
    const v = ref.current;
    if (!v) return;
    v.muted = !v.muted;
    if (!v.muted) {
      v.currentTime = 0;
      v.play().catch(() => {});
    }
    setSound(!v.muted);
  };

  return (
    <figure className="col film">
      <div className="plate">
        <video
          ref={ref}
          muted
          loop
          playsInline
          preload="metadata"
          poster={asset("/poster.jpg")}
          aria-label="Radius Mono launch film: the name rounds from sharp to round, colourful glyphs change weight, and a line sweeps across code to round it."
        >
          <source src={asset("/radius-mono-launch.mp4")} type="video/mp4" />
        </video>
        <button className="sound" type="button" aria-pressed={sound} onClick={toggle}>
          <SoundIcon on={sound} />
          <span>{sound ? "Sound off" : "Sound on"}</span>
        </button>
      </div>
      <figcaption>The 16-second launch film, rendered with Radius Mono.</figcaption>
    </figure>
  );
}
