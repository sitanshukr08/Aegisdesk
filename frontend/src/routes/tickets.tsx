import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { DotMatrixText } from "@/components/DotMatrixText";
import { ConfidencePill } from "@/components/ConfidencePill";
import { loadTickets, saveTickets, type Ticket } from "@/lib/session";
import { Copy, Trash2, AlertTriangle, Check } from "lucide-react";

export const Route = createFileRoute("/tickets")({
  head: () => ({
    meta: [
      { title: "Tickets · DeskBot" },
      { name: "description", content: "Auto-escalated IT support tickets opened by DeskBot when retrieval confidence is low." },
      { property: "og:title", content: "Tickets · DeskBot" },
      { property: "og:description", content: "Auto-escalated tickets routed to the L1 service desk." },
    ],
  }),
  component: TicketsPage,
});

function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  useEffect(() => setTickets(loadTickets()), []);

  const clear = () => {
    setTickets([]);
    saveTickets([]);
  };

  const copy = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopied(id);
    setTimeout(() => setCopied((c) => (c === id ? null : c)), 700);
  };

  return (
    <PageShell>
      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <DotMatrixText className="text-[10px] text-muted-foreground">Escalations</DotMatrixText>
            <h1 className="mt-2 text-2xl font-medium">Open tickets</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Tickets are opened automatically when retrieval confidence falls below threshold.
            </p>
          </div>
          {tickets.length > 0 && (
            <button
              onClick={clear}
              className="inline-flex items-center gap-1.5 rounded-sm border border-border px-2.5 py-1 text-[10px] font-mono-dot text-muted-foreground hover:text-foreground"
            >
              <Trash2 className="h-3 w-3" /> Clear
            </button>
          )}
        </div>

        {tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border bg-card/40 px-6 py-16 text-center">
            <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            <DotMatrixText className="text-xs text-muted-foreground">No escalations</DotMatrixText>
            <p className="text-xs text-muted-foreground">
              When DeskBot can't answer with high confidence, a ticket lands here.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md border border-border bg-card/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40">
                <tr className="font-mono-dot text-[10px] text-muted-foreground">
                  <th className="px-4 py-2">Ticket</th>
                  <th className="px-4 py-2">When</th>
                  <th className="px-4 py-2">Query</th>
                  <th className="px-4 py-2">Confidence</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {tickets.map((t) => (
                  <tr key={t.id} className="relative hover:bg-muted/20">
                    <td className="relative px-4 py-3">
                      <span className="absolute inset-y-0 left-0 w-0.5 bg-accent" />
                      <code className="text-accent">{t.id}</code>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(t.ts).toLocaleString()}
                    </td>
                    <td className="max-w-[280px] truncate px-4 py-3 text-foreground" title={t.query}>
                      {t.query}
                    </td>
                    <td className="px-4 py-3">
                      <ConfidencePill value={t.confidence} animate={false} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => copy(t.id)}
                        className="rounded p-1 text-muted-foreground hover:text-foreground"
                        aria-label="Copy ticket id"
                      >
                        {copied === t.id ? (
                          <Check className="h-3 w-3 text-primary" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageShell>
  );
}