import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { AskBar } from "@/components/AskBar";
import { DotMatrixText } from "@/components/DotMatrixText";
import { MessageSquare, ImageDown, BookOpen, AlertTriangle, ArrowUpRight } from "lucide-react";
import { getSessionId, loadThread, type Message } from "@/lib/session";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DeskBot — IT support, answered." },
      {
        name: "description",
        content:
          "DeskBot is an AI IT-support assistant: streaming RAG answers, screenshot understanding, and automatic ticket escalation.",
      },
      { property: "og:title", content: "DeskBot — IT support, answered." },
      {
        property: "og:description",
        content: "An AI IT helpdesk console — ask, attach a screenshot, escalate.",
      },
    ],
  }),
  component: Index,
});

const tiles = [
  { to: "/ask", label: "Ask", desc: "Streaming RAG answers with session memory.", icon: MessageSquare },
  { to: "/ask", label: "Screenshot", desc: "Drop a screenshot, get the error parsed.", icon: ImageDown },
  { to: "/knowledge", label: "Knowledge", desc: "Ingest TXT or PDF docs into the vector store.", icon: BookOpen },
  { to: "/tickets", label: "Escalate", desc: "Auto-routed tickets when confidence is low.", icon: AlertTriangle },
] as const;

const wordmark = "DESKBOT".split("");

function Index() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [sid, setSid] = useState("");
  const [recent, setRecent] = useState<Message[]>([]);

  useEffect(() => {
    setSid(getSessionId());
    const thread = loadThread().filter((m) => m.role === "user").slice(-3).reverse();
    setRecent(thread);
  }, []);

  const submit = (v: string) => {
    navigate({ to: "/ask", search: { q: v } });
  };

  return (
    <PageShell>
      <section className="mx-auto flex max-w-3xl flex-col items-center px-4 pb-12 pt-20 text-center md:pt-28">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/50 px-3 py-1 animate-fade-up">
          <span className="h-1.5 w-1.5 rounded-full bg-accent pulse-dot" />
          <DotMatrixText className="text-[10px] text-muted-foreground">
            System online · session {sid.slice(0, 6) || "—"}
          </DotMatrixText>
        </div>

        <h1 className="font-mono-dot text-5xl leading-tight tracking-[0.04em] md:text-7xl">
          {wordmark.map((ch, i) => (
            <span
              key={i}
              className="inline-block animate-fade-up"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              {ch === "K" ? (
                <>
                  {ch}
                  <span className="text-accent">·</span>
                </>
              ) : (
                ch
              )}
            </span>
          ))}
        </h1>

        <p className="mt-4 max-w-xl text-sm text-muted-foreground md:text-base">
          IT support, answered. Streaming retrieval over your knowledge base,
          screenshot understanding, and zero-friction ticket escalation.
        </p>

        <div className="mt-10 w-full">
          <AskBar
            value={q}
            onChange={setQ}
            onSubmit={(v) => submit(v)}
            placeholder="Describe an issue, paste an error, or drop a screenshot…"
            size="lg"
            autoFocus
          />
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-[10px] font-mono-dot text-muted-foreground">
            <span>Try:</span>
            {["VPN won't connect", "Outlook keeps crashing", "BSOD on boot"].map((s) => (
              <button
                key={s}
                onClick={() => submit(s)}
                className="rounded-sm border border-border bg-card/40 px-2 py-1 transition-colors hover:border-primary/60 hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {recent.length > 0 && (
          <div className="mt-10 w-full text-left">
            <DotMatrixText className="mb-2 block text-[10px] text-muted-foreground">
              Recent
            </DotMatrixText>
            <ul className="divide-y divide-border/40 rounded-md border border-border bg-card/40">
              {recent.map((m) => (
                <li key={m.id}>
                  <button
                    onClick={() => submit(m.content)}
                    className="flex w-full items-center gap-3 px-3 py-2 text-left text-xs text-foreground/90 hover:bg-muted/40"
                  >
                    <span className="font-mono-dot text-[10px] text-muted-foreground">
                      {new Date(m.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="truncate">{m.content}</span>
                    <ArrowUpRight className="ml-auto h-3 w-3 shrink-0 text-muted-foreground" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="mx-auto grid max-w-5xl gap-3 px-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
        {tiles.map((t, i) => (
          <Link
            key={t.label}
            to={t.to}
            className="group corner-frame relative overflow-hidden rounded-md border border-border bg-card/40 p-4 transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:bg-card"
            style={{ animationDelay: `${200 + i * 60}ms` }}
          >
            <div className="pointer-events-none absolute inset-0 bg-dot-grid-fine opacity-20" />
            <div className="relative flex items-start justify-between">
              <span className="grid h-7 w-7 place-items-center rounded-sm border border-border bg-background/60 text-primary">
                <t.icon className="h-3.5 w-3.5" />
              </span>
              <DotMatrixText className="text-[10px] text-muted-foreground">
                0{i + 1}
              </DotMatrixText>
            </div>
            <div className="relative mt-8">
              <DotMatrixText className="text-xs">{t.label}</DotMatrixText>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{t.desc}</p>
              <span className="mt-3 inline-block h-px w-0 bg-accent transition-all duration-300 group-hover:w-8" />
            </div>
          </Link>
        ))}
      </section>
    </PageShell>
  );
}
