import type { ReactNode } from "react";
import { Icon } from "./Icon";
import { cn } from "../cn";

export function ChatBubble({
  side,
  author,
  children,
  className,
  quoteCard,
}: {
  side: "assistant" | "user";
  author?: string;
  children: ReactNode;
  className?: string;
  /** material block rendered inside the bubble (e.g. drafted slot text) */
  quoteCard?: ReactNode;
}) {
  const isAssistant = side === "assistant";
  return (
    <div className={cn("flex gap-2", isAssistant ? "items-start" : "flex-row-reverse items-start", className)} data-qa={isAssistant ? "chat-assistant" : "chat-user"}>
      {isAssistant ? (
        <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-tint" aria-hidden>
          <Icon name="auto_awesome" className="text-[16px] text-brand" />
        </span>
      ) : null}
      <div className={cn("max-w-[85%] rounded-xl px-3 py-2 text-body-md", isAssistant ? "rounded-tl-(--radius-input) border border-border bg-card text-ink" : "bg-brand-tint text-ink")}>
        {isAssistant && author && <span className="mb-1 block text-label-sm text-ink-2">{author}</span>}
        {quoteCard}
        {children}
      </div>
    </div>
  );
}

/** Material block shown inside an assistant bubble when drafting a slot. */
export function DraftQuote({ children, label = "Draft" }: { children: ReactNode; label?: string }) {
  return (
    <div className="mb-2 rounded-(--radius-input) border border-success bg-success-bg px-3 py-2">
      <span className="mb-1 block text-label-sm text-success" data-qa="drafting-chip">
        <Icon name="auto_awesome" className="mr-1 inline text-[12px]" />
        {label}
      </span>
      <span className="text-body-md text-ink">{children}</span>
    </div>
  );
}

export function QuickReplies({ replies, onPick, className }: { replies: string[]; onPick?: (r: string) => void; className?: string }) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)} data-qa="quick-replies">
      {replies.map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onPick?.(r)}
          className="rounded-pill border border-ink-2 bg-card px-3 py-1.5 text-label-lg text-ink-2 transition-colors duration-150 hover:border-ink hover:text-ink"
        >
          {r}
        </button>
      ))}
    </div>
  );
}
