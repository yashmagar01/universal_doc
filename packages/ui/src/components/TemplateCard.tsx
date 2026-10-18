import { cn } from "../cn";
import type { ReactNode } from "react";
import { Tag, type TagTone } from "./Tag";
import { Tooltip } from "./Tooltip";
import { Progress } from "./Progress";

export type TemplateStatus = "ready" | "needs-review" | "processing" | "failed";

const statusTag: Record<TemplateStatus, { tone: TagTone; label: string }> = {
  ready: { tone: "success", label: "Template ready" },
  "needs-review": { tone: "warning", label: "Needs review" },
  processing: { tone: "info", label: "Processing" },
  failed: { tone: "error", label: "Failed" },
};

export function TemplateCard({
  name,
  meta,
  status,
  progressPercent,
  actions,
  menu,
  className,
  pageThumb,
  kindTag,
}: {
  name: string;
  /** "12 layers extracted · 2 pages · Last used 3 days ago" — computed by caller */
  meta: string;
  status: TemplateStatus;
  /** 0–100 while processing (computed) */
  progressPercent?: number;
  actions?: ReactNode;
  menu?: ReactNode;
  className?: string;
  /** simple schematic page-1 thumbnail (real raster once rendering lands in M3) */
  pageThumb?: ReactNode;
  kindTag?: string;
}) {
  const st = statusTag[status];
  return (
    <Tooltip content={name}>
      <article
        className={cn("flex flex-col rounded-(--radius-card) bg-card shadow-l1 hover:shadow-l2", className)}
        data-qa="template-card"
      >
        <div className="relative m-3 mb-0 aspect-16/10 overflow-hidden rounded-(--radius-input) border border-border bg-canvas">
          {pageThumb ?? <TemplateThumbFallback />}
          <span className="absolute top-2 right-2">
            <Tag tone={st.tone} className="shadow-sm">
              {st.label}
            </Tag>
          </span>
          {kindTag && (
            <span className="absolute bottom-2 left-2">
              <Tag tone="neutral">{kindTag}</Tag>
            </span>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-0.5 px-4 pt-3">
          <h3 className="truncate text-headline-md text-ink">{name}</h3>
          <p className="text-body-sm text-ink-2">{meta}</p>
        </div>
        {status === "processing" && progressPercent != null && (
          <div className="px-4 pt-3">
            <Progress value={progressPercent} />
          </div>
        )}
        <footer className="flex items-center gap-2 px-4 py-3">
          {status === "ready" || status === "needs-review" ? (
            actions
          ) : (
            <div className="flex w-full items-center gap-2">
              {actions}
              <span className="ms-auto">{menu}</span>
            </div>
          )}
          {(status === "ready" || status === "needs-review") && menu != null && <span className="ms-auto">{menu}</span>}
        </footer>
      </article>
    </Tooltip>
  );
}

/** neutral schematic placeholder; replaced by real page rasters in M3 */
function TemplateThumbFallback() {
  return (
    <div aria-hidden className="flex h-full w-full flex-col gap-2 p-3">
      <div className="h-2.5 w-3/5 rounded bg-border" />
      <div className="h-2 w-4/5 rounded bg-divider" />
      <div className="h-2 w-2/5 rounded bg-divider" />
      <div className="mt-auto h-9 w-full rounded bg-card" />
    </div>
  );
}
