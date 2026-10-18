import type { ReactNode } from "react";
import { cn } from "../cn";
import { Icon } from "./Icon";
export function Card({
  title,
  titleIcon,
  action,
  footer,
  className,
  bodyClassName,
  children,
  as: Tag = "div",
}: {
  title?: ReactNode;
  titleIcon?: ReactNode;
  action?: ReactNode;
  footer?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
  /** HTML element/landmark for the card root */
  as?: "div" | "aside" | "section";
}) {
  const Root = Tag;
  return (
    <Root className={cn("block rounded-(--radius-card) bg-card shadow-l1", className)}>
      {title != null && (
        <div className="flex items-start justify-between gap-2 px-4 pt-4">
          <h2 className="flex items-center gap-2 text-headline-md">
            {titleIcon}
            {title}
          </h2>
          {action}
        </div>
      )}
      <div className={cn(title == null ? "p-4" : "px-4 pt-4 pb-4", bodyClassName)}>{children}</div>
      {footer != null && <div className="flex items-center gap-2 border-t border-divider px-4 py-3">{footer}</div>}
    </Root>
  );
}

export function FileChip({
  name,
  meta,
  className,
}: {
  name: string;
  meta?: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-9 max-w-80 items-center gap-2 rounded-pill bg-canvas px-3 text-body-sm text-ink select-none",
        className,
      )}
      title={name}
    >
      <Icon name="description" className="text-ink-2 shrink-0" />
      <span className="max-w-56 truncate">{name}</span>
      {meta != null && <span className="text-body-sm whitespace-nowrap text-ink-2">{meta}</span>}
    </span>
  );
}

/** role-class → overlay token (design.md §2.1) */
export const roleOverlayClass: Record<string, string> = {
  headings: "border-ov-heading",
  text: "border-ov-text",
  media: "border-ov-media",
  shape: "border-ov-shape border-dashed",
  review: "border-ov-review border-dashed",
};

export const roleOverlayText: Record<string, string> = {
  headings: "text-ov-heading",
  text: "text-ov-text",
  media: "text-ov-media",
  shape: "text-ov-shape",
  review: "text-ov-review",
};

