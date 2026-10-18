import { Icon } from "./Icon";
import { IconButton } from "./IconButton";
import { cn } from "../cn";

export type Zoom = { value: number; set: (v: number) => void; step: (dir: 1 | -1) => void; fit: () => void };

/** Floating pill toolbar for canvas panes; panes get pb-24 so content is never covered (design.md §4). */
export function FloatingToolbar({
  zoom,
  page,
  toggles,
  className,
}: {
  zoom: Zoom;
  page?: { label: string; prev?: () => void; next?: () => void };
  toggles?: { key: string; label: string; icon: "grid_4x4" | "palette" | "rule" | "layers"; checked: boolean; onChange: (v: boolean) => void }[];
  className?: string;
}) {
  return (
    <div
      className={cn("pointer-events-auto flex h-11 items-center gap-1 rounded-pill bg-card px-2 shadow-l3", className)}
      data-qa="floating-toolbar"
      role="toolbar"
      aria-label="Canvas controls"
    >
      <IconButton icon="remove" label="Zoom out" onClick={() => zoom.step(-1)} />
      <label className="flex items-center gap-1 px-1 text-label-md text-ink-2">
        <span className="sr-only">Zoom percentage</span>
        <input
          type="number"
          value={zoom.value}
          onChange={(e) => zoom.set(Number(e.target.value) || 100)}
          step={10}
          min={25}
          max={400}
          className="w-14 rounded-(--radius-input) border border-transparent bg-canvas px-1.5 py-1 text-center text-label-md text-ink tabular-nums hover:border-border focus:border-brand focus:outline-none"
          aria-label="Zoom percent"
        />
        %
      </label>
      <IconButton icon="add" label="Zoom in" onClick={() => zoom.step(1)} />
      <IconButton icon="fit_screen" label="Fit to screen" onClick={zoom.fit} />
      {page != null && (
        <>
          <span className="mx-1 h-6 w-px bg-divider" />
          <IconButton icon="arrow_back" label="Previous page" onClick={page.prev} />
          <span className="text-label-md whitespace-nowrap text-ink tabular-nums" aria-live="polite">
            {page.label}
          </span>
          <IconButton icon="arrow_forward" label="Next page" onClick={page.next} />
        </>
      )}
      {toggles != null && toggles.length > 0 && (
        <>
          <span className="mx-1 h-6 w-px bg-divider" />
          {toggles.map((t) => (
            <IconToggle key={t.key} label={t.label} checked={t.checked} onChange={(v) => t.onChange(v)}>
              <Icon name={t.icon} />
            </IconToggle>
          ))}
        </>
      )}
    </div>
  );
}

function IconToggle({ label, checked, onChange, children }: { label: string; checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4",
        checked && "bg-brand-tint text-brand",
      )}
    >
      {children}
    </button>
  );
}
