import { useEffect, useRef, useState } from "react";
import { Paperclip, ArrowUp, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (v: string, file: File | null) => void;
  busy?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  size?: "lg" | "md";
}

export function AskBar({
  value,
  onChange,
  onSubmit,
  busy,
  placeholder = "Ask DeskBot about an IT issue…",
  autoFocus,
  size = "md",
}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  const submit = () => {
    const v = value.trim();
    if (!v || busy) return;
    onSubmit(v, file);
    setFile(null);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f && f.type.startsWith("image/")) setFile(f);
      }}
      className={cn(
        "group relative w-full rounded-md border bg-card/60 backdrop-blur transition-colors",
        dragOver ? "border-accent" : "border-border focus-within:border-primary/60",
      )}
    >
      <span
        className={cn(
          "pointer-events-none absolute inset-x-0 -top-px h-px",
          busy ? "bg-accent hairline-live" : "bg-transparent",
        )}
      />
      <div className="pointer-events-none absolute inset-0 rounded-md bg-dot-grid-fine opacity-30" />
      {file && (
        <div className="relative flex items-center justify-between gap-2 border-b border-border/60 px-3 py-2 text-xs">
          <div className="flex items-center gap-2 truncate text-muted-foreground">
            <Paperclip className="h-3 w-3" />
            <span className="truncate">{file.name}</span>
            <span className="font-mono-dot text-[10px]">{(file.size / 1024).toFixed(0)}KB</span>
          </div>
          <button
            onClick={() => setFile(null)}
            className="rounded p-0.5 text-muted-foreground hover:text-foreground"
            aria-label="Remove attachment"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}
      <div className="relative flex items-end gap-2 px-3 py-2.5">
        <button
          onClick={() => fileRef.current?.click()}
          className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Attach screenshot"
          type="button"
        >
          <Paperclip className="h-4 w-4" />
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          rows={1}
          placeholder={placeholder}
          className={cn(
            "flex-1 resize-none bg-transparent outline-none placeholder:text-muted-foreground/60",
            size === "lg" ? "py-1.5 text-base" : "py-1 text-sm",
          )}
          style={{ maxHeight: 160 }}
        />
        <button
          onClick={submit}
          disabled={busy || !value.trim()}
          className={cn(
            "inline-flex h-8 w-8 items-center justify-center rounded-sm border border-border bg-foreground text-background transition-all",
            "hover:bg-primary hover:text-primary-foreground disabled:opacity-30",
          )}
          aria-label="Send"
        >
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ArrowUp className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}