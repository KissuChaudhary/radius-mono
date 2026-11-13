"use client";

import type { CSSProperties } from "react";

type Props = {
  id: string;
  min: number;
  max: number;
  value: number;
  onChange: (v: number) => void;
  label?: string;
  step?: number;
};

/** Native range input with the filled-track percentage exposed to CSS. */
export default function Range({ id, min, max, value, onChange, label, step = 1 }: Props) {
  const p = ((value - min) / (max - min)) * 100;
  return (
    <input
      id={id}
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      aria-label={label}
      style={{ "--p": `${p}%` } as CSSProperties}
      onChange={(e) => onChange(Number(e.target.value))}
    />
  );
}
