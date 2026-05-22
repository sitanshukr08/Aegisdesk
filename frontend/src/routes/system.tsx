import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { DotMatrixText } from "@/components/DotMatrixText";
import { health } from "@/lib/api";
import { API_BASE_URL, APP_VERSION, isMockMode } from "@/lib/config";
import { resetSession, getSessionId } from "@/lib/session";
import { RefreshCw, Check, X, Loader2 } from "lucide-react";

export const Route = createFileRoute("/system")({
  head: () => ({
    meta: [
      { title: "System · DeskBot" },
      { name: "description", content: "DeskBot system status, API endpoint configuration, and session controls." },
      { property: "og:title", content: "System · DeskBot" },
      { property: "og:description", content: "Backend status, API base URL, and session controls." },
    ],
  }),
  component: SystemPage,
});

const URL_OVERRIDE_KEY = "deskbot.api_base_url_override";

function SystemPage() {
  const [status, setStatus] = useState<"ok" | "down" | "loading">("loading");
  const [latency, setLatency] = useState<number | null>(null);
  const [sid, setSid] = useState("");
  const [override, setOverride] = useState("");
  const [testing, setTesting] = useState<null | "ok" | "fail" | "loading">(null);

  const ping = async () => {
    setStatus("loading");
    const t0 = performance.now();
    try {
      await health();
      setLatency(Math.round(performance.now() - t0));
      setStatus("ok");
    } catch {
      setStatus("down");
    }
  };

  useEffect(() => {
    setSid(getSessionId());
    setOverride(localStorage.getItem(URL_OVERRIDE_KEY) ?? "");
    void ping();
  }, []);

  const saveOverride = () => {
    const cleaned = override.trim().replace(/\/$/, "");
    if (cleaned) localStorage.setItem(URL_OVERRIDE_KEY, cleaned);
    else localStorage.removeItem(URL_OVERRIDE_KEY);
    window.location.reload();
  };

  const testUrl = async () => {
    const cleaned = override.trim().replace(/\/$/, "");
    if (!cleaned) return;
    setTesting("loading");
    try {
      const res = await fetch(`${cleaned}/health`);
      setTesting(res.ok ? "ok" : "fail");
    } catch {
      setTesting("fail");
    }
  };

  const effectiveUrl =
    (typeof window !== "undefined" && localStorage.getItem(URL_OVERRIDE_KEY)) || API_BASE_URL || "";

  return (
    <PageShell>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <DotMatrixText className="text-[10px] text-muted-foreground">System</DotMatrixText>
        <h1 className="mt-2 text-2xl font-medium">Diagnostics</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Health, configuration, and session controls. Settings are stored locally in your browser.
        </p>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <Card label="Backend">
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  status === "ok"
                    ? "bg-accent pulse-dot"
                    : status === "down"
                      ? "bg-destructive"
                      : "bg-muted-foreground"
                }`}
              />
              <span className="text-sm">
                {isMockMode() && !effectiveUrl
                  ? "Mock mode (no backend)"
                  : status === "ok"
                    ? "Online"
                    : status === "down"
                      ? "Offline"
                      : "Checking…"}
              </span>
              <button
                onClick={ping}
                className="ml-auto rounded p-1 text-muted-foreground hover:text-foreground"
                aria-label="Ping again"
              >
                <RefreshCw className="h-3 w-3" />
              </button>
            </div>
            {latency != null && status === "ok" && (
              <p className="mt-1.5 text-[10px] font-mono-dot text-muted-foreground">{latency}ms</p>
            )}
          </Card>
          <Card label="Version">
            <span className="text-sm">{APP_VERSION}</span>
          </Card>

          <Card label="API base URL" wide>
            <code className="block truncate text-xs">{effectiveUrl || "(unset — using mock)"}</code>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                value={override}
                onChange={(e) => setOverride(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 rounded-sm border border-border bg-background px-2 py-1.5 font-mono text-xs outline-none focus:border-primary/60"
              />
              <div className="flex gap-2">
                <button
                  onClick={testUrl}
                  className="inline-flex items-center gap-1.5 rounded-sm border border-border px-2.5 py-1.5 text-[10px] font-mono-dot text-muted-foreground hover:text-foreground"
                >
                  {testing === "loading" ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : testing === "ok" ? (
                    <Check className="h-3 w-3 text-primary" />
                  ) : testing === "fail" ? (
                    <X className="h-3 w-3 text-accent" />
                  ) : null}
                  Test
                </button>
                <button
                  onClick={saveOverride}
                  className="inline-flex items-center rounded-sm border border-primary/40 bg-primary/10 px-2.5 py-1.5 text-[10px] font-mono-dot text-primary hover:bg-primary/20"
                >
                  Save &amp; reload
                </button>
              </div>
            </div>
            <p className="mt-2 text-[10px] text-muted-foreground">
              Overrides the build-time <code className="font-mono">VITE_API_BASE_URL</code>. Empty value clears the override.
            </p>
          </Card>

          <Card label="Session ID" wide>
            <code className="block truncate text-xs">{sid}</code>
            <button
              onClick={() => {
                resetSession();
                setSid(getSessionId());
              }}
              className="mt-3 inline-flex items-center gap-1.5 rounded-sm border border-border px-2 py-1 text-[10px] font-mono-dot text-muted-foreground hover:text-foreground"
            >
              Reset session
            </button>
          </Card>
        </div>

        <div className="mt-8 rounded-md border border-border bg-card/40 p-4">
          <DotMatrixText className="text-[10px] text-muted-foreground">Backend endpoints</DotMatrixText>
          <ul className="mt-3 space-y-1.5 font-mono text-xs text-foreground/90">
            <li><span className="text-primary">POST</span> /query — streaming RAG answer</li>
            <li><span className="text-primary">POST</span> /query_with_image — vision + answer</li>
            <li><span className="text-primary">POST</span> /ingest — add doc to KB</li>
            <li><span className="text-primary">GET </span> /health — liveness</li>
          </ul>
        </div>

        <div className="mt-8 rounded-md border border-border bg-card/40 p-4">
          <DotMatrixText className="text-[10px] text-muted-foreground">Connect a backend</DotMatrixText>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-xs leading-relaxed text-foreground/90">
            <li>
              Run the DeskBot FastAPI server from the <code className="font-mono">annshrunes/deskbot</code> repo:
              <pre className="mt-1 overflow-x-auto rounded-sm bg-background/60 p-2 font-mono text-[11px]">uvicorn app.main:app --reload --host 0.0.0.0 --port 8000</pre>
            </li>
            <li>
              Enable CORS for the Lovable origin in <code className="font-mono">app/main.py</code> using
              <code className="font-mono"> CORSMiddleware</code> with
              <code className="font-mono"> allow_origins=["*"]</code> (or your specific origins).
            </li>
            <li>
              Either set <code className="font-mono">VITE_API_BASE_URL=http://localhost:8000</code> at build time, or paste the URL above and click <em>Save &amp; reload</em>.
            </li>
            <li>
              Hit <em>Test</em> first to verify <code className="font-mono">/health</code> responds — then ask a question on the Ask page.
            </li>
          </ol>
        </div>
      </div>
    </PageShell>
  );
}

function Card({ label, children, wide }: { label: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={`rounded-md border border-border bg-card/40 p-4 ${wide ? "sm:col-span-2" : ""}`}>
      <DotMatrixText className="mb-3 block text-[10px] text-muted-foreground">{label}</DotMatrixText>
      {children}
    </div>
  );
}
