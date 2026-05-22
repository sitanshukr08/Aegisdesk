import { Header } from "./Header";
import { MatrixBackground } from "./MatrixBackground";
import { APP_VERSION } from "@/lib/config";

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <MatrixBackground />
      <div className="pointer-events-none fixed inset-0 z-[1] scanline" />
      <div className="relative z-10 flex flex-1 flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border/60 px-4 py-3">
          <div className="mx-auto flex max-w-6xl items-center justify-between text-[10px] font-mono-dot text-muted-foreground">
            <span>HCLTech · AI DeskBot</span>
            <span>{APP_VERSION}</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
