import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { Tooltip } from "./Tooltip";
import { cn } from "../cn";

/** 32-px footer status bar. All values computed by callers via /status (FR-SYS-02). */
export function StatusBar({
  left,
  right,
  privacyMode,
  version,
}: {
  left: { engine: string; detail?: string; ram?: string; parser?: string };
  right?: ReactNode;
  privacyMode: string;
  version: string;
}) {
  return (
    <footer
      data-qa="status-bar"
      className="sticky bottom-0 z-30 h-8 bg-card px-6 text-label-sm text-ink-2 shadow-[0_-1px_0_var(--color-border)]"
    >
      <div className="flex h-full items-center gap-3 whitespace-nowrap">
        <span className="flex items-center gap-1.5 text-ink">
          <Icon name="brightness_1" className="text-[10px] text-success" fill />
          {left.engine}
        </span>
        {left.detail && <span>{left.detail}</span>}
        {left.ram && (
          <span className="tabular-nums">
            <span className="sr-only">Memory used: </span>RAM {left.ram}
          </span>
        )}
        {left.parser && <span>{left.parser}</span>}
        <span className="ms-auto flex items-center gap-3">
          {right}
          <Tooltip content="Templix sends nothing on its own. Cloud providers are only contacted when you choose a cloud model.">
            <span className="flex items-center gap-1">
              <Icon name="shield" className="text-[14px]" />
              {privacyMode}
            </span>
          </Tooltip>
          <a href="#shortcuts" className="hover:text-ink">
            Keyboard Shortcuts (?)
          </a>
          <a href="#docs" className="hover:text-ink">
            Documentation
          </a>
          <a href="#help" className="hover:text-ink">
            Help &amp; Privacy
          </a>
          <span className="font-mono tabular-nums">v{version}</span>
        </span>
      </div>
    </footer>
  );
}

export function Dot({ tone = "success", className }: { tone?: "success" | "warning" | "error" | "neutral"; className?: string }) {
  const colors = { success: "bg-success", warning: "bg-warning", error: "bg-error", neutral: "bg-border-strong" };
  return <span aria-hidden className={cn("inline-block size-2 rounded-full", colors[tone], className)} />;
}

export function StatusPill({ tone, icon, children }: { tone: "success" | "warning" | "error" | "neutral"; icon?: IconName; children: ReactNode }) {
  const map = {
    success: "bg-success-bg text-success",
    warning: "bg-warning-bg text-warning",
    error: "bg-error-bg text-error",
    neutral: "bg-canvas text-ink-2",
  } as const;
  return (
    <span className={cn("inline-flex h-6 items-center gap-1 rounded-pill px-2.5 text-label-sm", map[tone])}>
      {icon && <Icon name={icon} className="text-[14px]" />}
      {children}
    </span>
  );
}
