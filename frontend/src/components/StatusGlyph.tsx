import { useEffect, useState } from "react";
import { health } from "@/lib/api";
import { isMockMode } from "@/lib/config";
import { cn } from "@/lib/utils";

export function StatusGlyph({ className }: { className?: string }) {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        await health();
        if (alive) setOk(true);
      } catch {
        if (alive) setOk(false);
      }
    };
    check();
    const id = setInterval(check, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);
  const label = isMockMode() ? "DEMO" : ok ? "LIVE" : ok === false ? "OFFLINE" : "…";
  const color = isMockMode()
    ? "bg-muted-foreground"
    : ok
      ? "bg-accent pulse-dot"
      : ok === false
        ? "bg-destructive"
        : "bg-muted-foreground";
  return (
    <div className={cn("inline-flex items-center gap-2 text-[10px] font-mono-dot text-muted-foreground", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", color)} />
      {label}
    </div>
  );
}