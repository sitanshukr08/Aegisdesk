import type { Message } from "@/lib/session";
import { ConfidencePill } from "./ConfidencePill";
import { DotMatrixText } from "./DotMatrixText";
import { AlertTriangle, Image as ImageIcon, User, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThreadMessage({ message, streaming }: { message: Message; streaming?: boolean }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3 px-1 py-4", isUser ? "" : "border-t border-border/40")}>
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-sm border",
          isUser ? "border-border bg-muted text-muted-foreground" : "border-primary/40 bg-primary/10 text-primary",
        )}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Cpu className="h-3.5 w-3.5" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1.5 flex items-center gap-2">
          <DotMatrixText className="text-[10px] text-muted-foreground">
            {isUser ? "You" : "DeskBot"}
          </DotMatrixText>
          {!isUser && message.meta?.intent && (
            <span className="rounded-sm border border-border px-1.5 py-0.5 text-[10px] font-mono-dot text-muted-foreground">
              {message.meta.intent.replace("_", " ")}
            </span>
          )}
          {!isUser && typeof message.meta?.confidence === "number" && !streaming && (
            <ConfidencePill value={message.meta.confidence} />
          )}
        </div>
        {message.attachment && (
          <div className="mb-3 flex items-center gap-2 rounded-sm border border-border bg-muted/40 p-2 text-xs">
            <ImageIcon className="h-3 w-3 text-muted-foreground" />
            <img
              src={message.attachment.dataUrl}
              alt={message.attachment.name}
              className="h-12 w-12 rounded-sm border border-border object-cover"
            />
            <span className="truncate text-muted-foreground">{message.attachment.name}</span>
          </div>
        )}
        <div
          className={cn(
            "whitespace-pre-wrap text-sm leading-relaxed",
            isUser ? "text-foreground" : "text-foreground/90",
            streaming && "caret-blink",
          )}
        >
          {!isUser && streaming && !message.content ? (
            <span className="inline-flex items-center gap-1 text-muted-foreground">
              <span className="h-1 w-1 animate-bounce rounded-full bg-current [animation-delay:0ms]" />
              <span className="h-1 w-1 animate-bounce rounded-full bg-current [animation-delay:120ms]" />
              <span className="h-1 w-1 animate-bounce rounded-full bg-current [animation-delay:240ms]" />
            </span>
          ) : (
            message.content
          )}
        </div>
        {!isUser && message.meta?.escalate && message.meta.ticket_id && (
          <div className="mt-3 flex items-center gap-2 rounded-sm border border-accent/40 bg-accent/5 px-3 py-2">
            <AlertTriangle className="h-3.5 w-3.5 text-accent" />
            <DotMatrixText className="text-[10px] text-accent">Escalated</DotMatrixText>
            <code className="ml-auto font-mono text-xs text-foreground">{message.meta.ticket_id}</code>
          </div>
        )}
      </div>
    </div>
  );
}