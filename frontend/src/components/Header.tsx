import { Link, useRouterState } from "@tanstack/react-router";
import { DotMatrixText } from "./DotMatrixText";
import { StatusGlyph } from "./StatusGlyph";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Home" },
  { to: "/ask", label: "Ask" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/tickets", label: "Tickets" },
  { to: "/system", label: "System" },
] as const;

export function Header() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <header className="sticky top-0 z-30 border-b border-border/60 bg-background/70 backdrop-blur">
      <div className="mx-auto flex h-12 max-w-6xl items-center gap-6 px-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="grid h-5 w-5 grid-cols-3 grid-rows-3 gap-px">
            {Array.from({ length: 9 }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  "rounded-[1px]",
                  [0, 2, 4, 6, 8].includes(i) ? "bg-foreground" : "bg-foreground/20",
                )}
              />
            ))}
          </div>
          <DotMatrixText className="text-xs">DeskBot</DotMatrixText>
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => {
            const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "relative rounded-sm px-2.5 py-1 text-xs font-mono-dot transition-colors",
                  active
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
                <span
                  className={cn(
                    "absolute left-2.5 right-2.5 -bottom-[7px] h-px transition-all duration-300",
                    active ? "bg-accent opacity-100" : "bg-transparent opacity-0",
                  )}
                />
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden items-center gap-1 rounded-sm border border-border px-1.5 py-0.5 text-[10px] font-mono-dot text-muted-foreground sm:inline-flex">
            <kbd className="font-mono">⌘</kbd>
            <kbd className="font-mono">K</kbd>
          </span>
          <StatusGlyph />
        </div>
      </div>
    </header>
  );
}
