import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { z } from "zod";
import { PageShell } from "@/components/PageShell";
import { AskBar } from "@/components/AskBar";
import { ThreadMessage } from "@/components/ThreadMessage";
import { DotMatrixText } from "@/components/DotMatrixText";
import { ConfidencePill } from "@/components/ConfidencePill";
import { streamQuery } from "@/lib/api";
import {
  getSessionId,
  loadThread,
  saveThread,
  loadTickets,
  saveTickets,
  newId,
  type Message,
  type Ticket,
} from "@/lib/session";
import { Sparkles, RotateCw } from "lucide-react";

const searchSchema = z.object({ q: z.string().optional() });

export const Route = createFileRoute("/ask")({
  head: () => ({
    meta: [
      { title: "Ask · DeskBot" },
      { name: "description", content: "Conversational IT support with streaming answers and screenshot understanding." },
      { property: "og:title", content: "Ask · DeskBot" },
      { property: "og:description", content: "Conversational IT support — streaming answers, screenshot vision." },
    ],
  }),
  validateSearch: searchSchema,
  component: AskPage,
});

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result as string);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}

function AskPage() {
  const { q: initialQ } = Route.useSearch();
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState("");
  const scrollerRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setSessionId(getSessionId());
    setMessages(loadThread());
  }, []);

  useEffect(() => {
    if (messages.length) saveThread(messages);
  }, [messages]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, streamingId]);

  const send = async (text: string, file: File | null) => {
    if (!text.trim() || streamingId) return;
    const sid = sessionId || getSessionId();
    const userMsg: Message = {
      id: newId(),
      role: "user",
      content: text,
      ts: Date.now(),
      attachment: file ? { name: file.name, dataUrl: await fileToDataUrl(file) } : undefined,
    };
    const botMsg: Message = {
      id: newId(),
      role: "assistant",
      content: "",
      ts: Date.now(),
      meta: { confidence: 0, escalate: false, ticket_id: null },
    };
    setMessages((m) => [...m, userMsg, botMsg]);
    setInput("");
    setStreamingId(botMsg.id);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      let acc = "";
      let lastMeta: Message["meta"] = botMsg.meta;
      for await (const block of streamQuery(sid, text, { file, signal: controller.signal })) {
        acc += block.chunk;
        lastMeta = {
          confidence: block.meta.confidence,
          escalate: block.meta.escalate,
          ticket_id: block.meta.ticket_id,
          intent: block.meta.intent,
        };
        setMessages((m) =>
          m.map((x) => (x.id === botMsg.id ? { ...x, content: acc, meta: lastMeta } : x)),
        );
      }
      if (lastMeta?.escalate && lastMeta.ticket_id) {
        const t: Ticket = {
          id: lastMeta.ticket_id,
          ts: Date.now(),
          query: text,
          confidence: lastMeta.confidence ?? 0,
        };
        const cur = loadTickets();
        saveTickets([t, ...cur]);
      }
    } catch (e) {
      setMessages((m) =>
        m.map((x) =>
          x.id === botMsg.id
            ? { ...x, content: `Connection failed: ${(e as Error).message}` }
            : x,
        ),
      );
    } finally {
      setStreamingId(null);
      abortRef.current = null;
    }
  };

  useEffect(() => {
    if (startedRef.current) return;
    if (initialQ && sessionId) {
      startedRef.current = true;
      void send(initialQ, null);
      navigate({ to: "/ask", search: {}, replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ, sessionId]);

  const latest = useMemo(() => [...messages].reverse().find((m) => m.role === "assistant"), [messages]);

  const clearThread = () => {
    setMessages([]);
    saveThread([]);
  };

  const stop = () => {
    abortRef.current?.abort();
  };

  return (
    <PageShell>
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[1fr_280px]">
        <div className="flex min-h-[70vh] flex-col">
          <div className="mb-3 flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              <DotMatrixText className="text-xs">Ask Console</DotMatrixText>
              {streamingId && (
                <span className="ml-2 inline-flex items-center gap-1.5 rounded-sm border border-accent/40 px-1.5 py-0.5 text-[10px] font-mono-dot text-accent">
                  <span className="h-1 w-1 rounded-full bg-accent pulse-dot" />
                  Streaming
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {streamingId && (
                <button
                  onClick={stop}
                  className="inline-flex items-center gap-1.5 rounded-sm border border-accent/50 px-2 py-1 text-[10px] font-mono-dot text-accent hover:bg-accent/10"
                >
                  Stop
                </button>
              )}
              <button
                onClick={clearThread}
                className="inline-flex items-center gap-1.5 rounded-sm border border-border px-2 py-1 text-[10px] font-mono-dot text-muted-foreground hover:text-foreground"
              >
                <RotateCw className="h-3 w-3" /> Clear
              </button>
            </div>
          </div>

          <div ref={scrollerRef} className="min-h-0 flex-1 overflow-y-auto pr-1">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-3 py-12 text-center text-sm text-muted-foreground">
                <div className="grid grid-cols-5 grid-rows-5 gap-1 opacity-40">
                  {Array.from({ length: 25 }).map((_, i) => (
                    <span key={i} className="h-1.5 w-1.5 rounded-full bg-foreground" />
                  ))}
                </div>
                <p>No thread yet. Ask anything below to begin.</p>
              </div>
            )}
            {messages.map((m) => (
              <ThreadMessage key={m.id} message={m} streaming={m.id === streamingId} />
            ))}
          </div>

          <div className="sticky bottom-0 mt-4 pb-2">
            <AskBar
              value={input}
              onChange={setInput}
              onSubmit={(v, f) => send(v, f)}
              busy={!!streamingId}
              autoFocus
            />
            <p className="mt-2 text-[10px] font-mono-dot text-muted-foreground">
              ↵ send · ⇧↵ newline · drop an image anywhere on the bar to attach
            </p>
          </div>
        </div>

        <aside className="hidden flex-col gap-3 lg:flex">
          <InspectorCard title="Session">
            <code className="block truncate text-xs text-foreground">{sessionId || "—"}</code>
          </InspectorCard>
          <InspectorCard title="Confidence">
            {latest?.meta?.confidence != null ? (
              <ConfidencePill value={latest.meta.confidence} animate={false} />
            ) : (
              <span className="text-xs text-muted-foreground">No answer yet</span>
            )}
          </InspectorCard>
          <InspectorCard title="Intent">
            <span className="text-xs text-foreground">{latest?.meta?.intent || "—"}</span>
          </InspectorCard>
          <InspectorCard title="Last ticket">
            {latest?.meta?.ticket_id ? (
              <code className="text-xs text-accent">{latest.meta.ticket_id}</code>
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </InspectorCard>
          <InspectorCard title="Pipeline">
            <ol className="space-y-1.5 text-[11px] text-muted-foreground">
              <li>1 · Intent routing</li>
              <li>2 · Query expansion</li>
              <li>3 · Two-stage retrieval</li>
              <li>4 · Streaming answer</li>
              <li>5 · Escalation gate</li>
            </ol>
          </InspectorCard>
        </aside>
      </div>
    </PageShell>
  );
}

function InspectorCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-card/40 p-3">
      <DotMatrixText className="mb-2 block text-[10px] text-muted-foreground">{title}</DotMatrixText>
      {children}
    </div>
  );
}