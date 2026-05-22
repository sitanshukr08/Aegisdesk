import { useEffect, useRef } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

/**
 * Nothing-style dot matrix that reacts to the cursor.
 * Updates CSS vars --mx/--my on pointermove (rAF-throttled), so no React re-renders.
 */
export function MatrixBackground() {
  const ref = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) return;

    // Initialize roughly centered
    el.style.setProperty("--mx", `${window.innerWidth / 2}px`);
    el.style.setProperty("--my", `${window.innerHeight / 2}px`);

    let raf = 0;
    let nx = 0;
    let ny = 0;
    const onMove = (e: PointerEvent) => {
      nx = e.clientX;
      ny = e.clientY;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        el.style.setProperty("--mx", `${nx}px`);
        el.style.setProperty("--my", `${ny}px`);
        raf = 0;
      });
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [reduced]);

  return (
    <div ref={ref} aria-hidden className="matrix-bg pointer-events-none fixed inset-0 z-0">
      {/* base static dot grid */}
      <div className="absolute inset-0 bg-dot-grid opacity-40" />
      {/* parallax fine grid */}
      <div className="matrix-parallax absolute inset-0 bg-dot-grid-fine opacity-20" />
      {/* bloom: bright dots near cursor */}
      <div className="matrix-bloom absolute inset-0" />
      {/* spotlight tint */}
      <div className="matrix-spotlight absolute inset-0" />
    </div>
  );
}
