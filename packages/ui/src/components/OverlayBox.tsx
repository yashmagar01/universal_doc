import { cn } from "../cn";
import { Icon } from "./Icon";

/** Absolutely-positioned overlay box on the analysis canvas (design.md §4 + §2.1). */
export function OverlayBox({
  x,
  y,
  w,
  h,
  roleClass,
  label,
  selected = false,
  review,
  handleCount = 8,
  handleClick,
  className,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  roleClass: "headings" | "text" | "media" | "shape" | "review";
  label: string;
  selected?: boolean;
  /** present only when review flagged (warning icon + text, never colour-only) */
  review?: string;
  handleCount?: 0 | 8;
  handleClick?: () => void;
  className?: string;
}) {
  const color = {
    headings: "border-ov-heading",
    text: "border-ov-text",
    media: "border-ov-media",
    shape: "border-ov-shape border-dashed",
    review: "border-ov-review border-dashed",
  }[roleClass];
  const labelColor = {
    headings: "bg-ov-heading",
    text: "bg-ov-text",
    media: "bg-ov-media",
    shape: "bg-ov-shape",
    review: "bg-ov-review",
  }[roleClass];
  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "absolute cursor-default border-[1.5px] bg-transparent p-0 leading-none",
        color,
        selected && "outline outline-(--color-brand) outline-1",
        className,
      )}
      style={{ left: x, top: y, width: w, height: h }}
      data-qa="overlay-box"
      data-role={roleClass}
      aria-pressed={selected}
    >
      <span
        className={cn(
          "absolute bottom-full left-0 mb-1 flex max-w-none items-center gap-1 rounded-(--radius-input) px-1 py-0.5 text-[10px] font-medium whitespace-nowrap text-white",
          labelColor,
        )}
      >
        {review && <Icon name="warning" className="text-[12px]" />}
        {label}
      </span>
      {selected &&
        handleCount === 8 &&
        (["-top-1 -left-1", "-top-1 left-1/2 -translate-x-1/2", "-top-1 -right-1", "top-1/2 -left-1 -translate-y-1/2", "top-1/2 -right-1 -translate-y-1/2", "-bottom-1 -left-1", "-bottom-1 left-1/2 -translate-x-1/2", "-bottom-1 -right-1"] as const).map(
          (pos) => (
            <span key={pos} className={cn("absolute size-2 border-[1.5px] bg-card", pos)} aria-hidden data-qa="overlay-handle" />
          ),
        )}
    </button>
  );
}
