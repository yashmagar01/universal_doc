import type { ReactNode } from "react";
import { Button } from "./Button";
import { Icon } from "./Icon";
import { cn } from "../cn";

/** Proposed-changes diff card (design.md §4). Content is data; text nodes only — no HTML. */
export function DiffCard({
  slotLabel,
  slotMeta,
  counter,
  counterTone = "safe",
  original,
  proposal,
  providerNote,
  targetNote,
  onAccept,
  onReject,
  media,
  className,
}: {
  slotLabel: string;
  slotMeta?: string;
  counter?: string;
  counterTone?: "safe" | "warn" | "over";
  original: ReactNode;
  proposal: ReactNode;
  providerNote?: string;
  targetNote?: string;
  onAccept?: () => void;
  onReject?: () => void;
  media?: { before: ReactNode; after: ReactNode };
  className?: string;
}) {
  return (
    <article className={cn("flex flex-col gap-2 rounded-(--radius-card) bg-card p-3 shadow-l1", className)} data-qa="diff-card">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <span className="block truncate text-label-lg text-ink">{slotLabel}</span>
          {slotMeta && <span className="text-body-sm text-ink-2">{slotMeta}</span>}
        </div>
        {counter && (
          <span
            className={cn(
              "shrink-0 rounded-pill px-2 py-0.5 text-label-sm",
              counterTone === "safe" && "bg-success-bg text-success",
              counterTone === "warn" && "bg-warning-bg text-warning",
              counterTone === "over" && "bg-error-bg text-error",
            )}
          >
            {counter}
          </span>
        )}
      </div>
      {media ? (
        <div className="grid grid-cols-2 gap-2">
          <figure className="m-0 overflow-hidden rounded-(--radius-input) border border-border bg-canvas">
            <figcaption className="bg-canvas px-2 py-1 text-label-sm text-ink-2">Before</figcaption>
            {media.before}
          </figure>
          <figure className="m-0 overflow-hidden rounded-(--radius-input) border border-success bg-canvas">
            <figcaption className="bg-canvas px-2 py-1 text-label-sm text-ink-2">After (auto-cropped)</figcaption>
            {media.after}
          </figure>
        </div>
      ) : (
        <>
          <div className="rounded-(--radius-input) bg-canvas px-3 py-2 text-body-sm text-ink-2 line-through">
            <span className="sr-only">Original (PDF source): </span>
            {original}
          </div>
          <div className="rounded-(--radius-input) border border-success bg-success-bg px-3 py-2 text-body-sm text-ink-2">
            <span className="sr-only">AI proposal: </span>
            <span className="text-ink">{proposal}</span>
          </div>
        </>
      )}
      {targetNote && (
        <p className="flex items-center gap-1 text-body-sm text-ink-2">
          <Icon name="rule" className="text-[14px]" /> {targetNote}
        </p>
      )}
      <div className="mt-1 flex justify-end gap-2">
        <Button variant="secondary" size="sm" onClick={onReject}>
          Reject
        </Button>
        <Button variant="primary" size="sm" onClick={onAccept}>
          Accept
        </Button>
      </div>
      {providerNote && <p className="sr-only">{providerNote}</p>}
    </article>
  );
}
