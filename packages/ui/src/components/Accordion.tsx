import type { ReactNode } from "react";
import { Icon } from "./Icon";
import { Tag, type TagTone } from "./Tag";
import { cn } from "../cn";

export type AccordionItemState = { label: string; tone?: TagTone; icon?: ReactNode };

// Controlled disclosure (open/onToggle) — no radix needed; a button + aria-expanded is the whole job.
export function AccordionSection({
  title,
  state,
  open,
  onToggle,
  children,
  className,
}: {
  title: ReactNode;
  state?: AccordionItemState;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("border-b border-divider last:border-b-0", className)}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        data-qa="section-header"
        className="flex h-11 w-full items-center gap-2 px-4 text-left hover:bg-black/2"
      >
        <Icon name="chevron_right" className={cn("text-ink-2 transition-transform duration-150", open && "rotate-90")} />
        <span className="flex-1 truncate text-label-lg text-ink">{title}</span>
        {state != null && (
          <Tag tone={state.tone ?? "neutral"} icon={state.icon}>
            {state.label}
          </Tag>
        )}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}
