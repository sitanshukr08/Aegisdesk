import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { DotMatrixText } from "@/components/DotMatrixText";
import { ingestFile } from "@/lib/api";
import { loadIngested, saveIngested, type IngestedDoc } from "@/lib/session";
import { Upload, FileText, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/knowledge")({
  head: () => ({
    meta: [
      { title: "Knowledge · DeskBot" },
      { name: "description", content: "Ingest TXT or PDF documents into the DeskBot vector knowledge base." },
      { property: "og:title", content: "Knowledge · DeskBot" },
      { property: "og:description", content: "Ingest TXT or PDF docs into the vector store." },
    ],
  }),
  component: KnowledgePage,
});

function KnowledgePage() {
  const [docs, setDocs] = useState<IngestedDoc[]>([]);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => setDocs(loadIngested()), []);

  const handleFiles = async (files: FileList | File[]) => {
    const list = Array.from(files);
    setBusy(true);
    for (const f of list) {
      try {
        await ingestFile(f);
        const next: IngestedDoc = { name: f.name, size: f.size, ts: Date.now(), status: "ok" };
        setDocs((d) => {
          const updated = [next, ...d];
          saveIngested(updated);
          return updated;
        });
      } catch {
        const next: IngestedDoc = { name: f.name, size: f.size, ts: Date.now(), status: "error" };
        setDocs((d) => {
          const updated = [next, ...d];
          saveIngested(updated);
          return updated;
        });
      }
    }
    setBusy(false);
  };

  return (
    <PageShell>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="mb-6">
          <DotMatrixText className="text-[10px] text-muted-foreground">Knowledge base</DotMatrixText>
          <h1 className="mt-2 text-2xl font-medium">Ingest documents</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Drop TXT or PDF files to add them to the retrieval index. Used by every future question.
          </p>
        </div>

        <label
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            if (e.dataTransfer.files?.length) void handleFiles(e.dataTransfer.files);
          }}
          className={cn(
            "corner-frame relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-md border bg-card/40 px-6 py-12 transition-colors",
            over ? "border-transparent marching-ants bg-accent/5" : "border-dashed border-border hover:border-primary/60",
          )}
        >
          <input
            type="file"
            multiple
            accept=".txt,.pdf"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <div className="grid grid-cols-4 grid-rows-4 gap-1 opacity-40">
            {Array.from({ length: 16 }).map((_, i) => (
              <span key={i} className="h-1 w-1 rounded-full bg-foreground" />
            ))}
          </div>
          <Upload className="h-5 w-5 text-primary" />
          <DotMatrixText className="text-xs">
            {busy ? "Ingesting…" : "Drop files or click to upload"}
          </DotMatrixText>
          <span className="text-[10px] font-mono-dot text-muted-foreground">TXT · PDF · max 20MB</span>
        </label>

        <div className="mt-8">
          <DotMatrixText className="mb-3 block text-[10px] text-muted-foreground">
            Recently ingested
          </DotMatrixText>
          <div className="overflow-hidden rounded-md border border-border bg-card/40">
            {docs.length === 0 ? (
              <div className="px-4 py-6 text-center text-xs text-muted-foreground">
                Nothing ingested yet.
              </div>
            ) : (
              <ul className="divide-y divide-border/60">
                {docs.map((d, i) => (
                  <li key={i} className="flex items-center gap-3 px-4 py-3 text-xs">
                    <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="truncate text-foreground">{d.name}</span>
                    <span className="ml-auto font-mono-dot text-[10px] text-muted-foreground">
                      {(d.size / 1024).toFixed(0)}KB
                    </span>
                    {d.status === "ok" ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-accent" />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        {busy && (
          <div className="mt-4 flex items-center gap-2 text-[11px] text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" /> Sending to vector store…
          </div>
        )}
      </div>
    </PageShell>
  );
}