import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function ConfidencePill({ value, animate = true }: { value: number; animate?: boolean }) {
  const target = Math.max(0, Math.min(1, value)) * 100;
  const [n, setN] = useState(animate ? 0 : target);
  useEffect(() => {
    if (!animate) {
      setN(target);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / 600);
      setN(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, animate]);

  const tone =
    target < 40
      ? "border-accent/40 text-accent"
      : target < 70
        ? "border-muted-foreground/40 text-muted-foreground"
        : "border-primary/40 text-primary";

  const R = 6;
  const C = 2 * Math.PI * R;
  const dash = (n / 100) * C;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-1.5 py-0.5 text-[10px] font-mono-dot",
        tone,
      )}
      title={`Confidence ${target.toFixed(1)}%`}
    >
      <svg width="14" height="14" viewBox="0 0 16 16" className="-ml-0.5">
        <circle cx="8" cy="8" r={R} fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="2" />
        <circle
          cx="8"
          cy="8"
          r={R}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${C}`}
          transform="rotate(-90 8 8)"
        />
      </svg>
      {n.toFixed(0)}%
    </span>
  );
}
