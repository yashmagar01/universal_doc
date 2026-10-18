import { cn } from "../cn";

export function Progress({
  value,
  max = 100,
  label,
  className,
}: {
  value: number;
  max?: number;
  label?: string;
  className?: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {label != null && <span className="text-body-sm text-ink-2">{label}</span>}
      <div
        role="progressbar"
        aria-label={label ?? "Progress"}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className="h-1.5 min-w-32 flex-1 overflow-hidden rounded-pill bg-divider"
      >
        <div className="h-full rounded-pill bg-brand transition-[width] duration-300" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-body-sm tabular-nums text-ink-2">{Math.round(pct)}%</span>
    </div>
  );
}
