import { forwardRef, type ReactNode } from "react";
import { cn } from "../cn";

export type TagTone = "success" | "info" | "warning" | "error" | "neutral" | "brand";

const toneClasses: Record<TagTone, string> = {
  success: "bg-success-bg text-success",
  info: "bg-brand-tint text-brand",
  warning: "bg-warning-bg text-warning",
  error: "bg-error-bg text-error",
  neutral: "bg-canvas text-ink-2",
  brand: "bg-brand text-white",
};

export const Tag = forwardRef<
  HTMLSpanElement,
  {
    tone?: TagTone;
    icon?: ReactNode;
    className?: string;
    children: ReactNode;
  }
>(function Tag({ tone = "neutral", icon, className, children }, ref) {
  return (
    <span
      ref={ref}
      className={cn(
        "inline-flex h-6 items-center gap-1 rounded-pill px-2.5 text-label-sm whitespace-nowrap select-none",
        toneClasses[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
});

export function FilterChip({
  active = false,
  onClick,
  children,
  className,
}: {
  active?: boolean;
  onClick?: () => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "inline-flex h-8 items-center rounded-pill px-4 text-label-lg whitespace-nowrap transition-colors duration-150 select-none",
        active ? "border border-transparent bg-brand text-white" : "border border-ink-2 bg-card text-ink-2 hover:border-ink hover:text-ink",
        className,
      )}
    >
      {children}
    </button>
  );
}
