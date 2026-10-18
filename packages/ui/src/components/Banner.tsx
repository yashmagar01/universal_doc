import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { cn } from "../cn";

export type BannerTone = "info" | "success" | "warning" | "error";

const toneStyles: Record<BannerTone, { box: string; icon: IconName; iconColor: string }> = {
  info: { box: "bg-brand-tint", icon: "info", iconColor: "text-brand" },
  success: { box: "bg-success-bg", icon: "check_circle", iconColor: "text-success" },
  warning: { box: "bg-warning-bg", icon: "warning", iconColor: "text-warning" },
  error: { box: "bg-error-bg", icon: "warning", iconColor: "text-error" },
};

export function Banner({
  tone = "info",
  icon,
  title,
  actions,
  className,
  role,
  children,
}: {
  tone?: BannerTone;
  icon?: ReactNode;
  title?: ReactNode;
  actions?: ReactNode;
  className?: string;
  /** defaults to "alert" for errors, "status" otherwise */
  role?: "status" | "alert";
  children: ReactNode;
}) {
  const s = toneStyles[tone];
  return (
    <div
      role={role ?? (tone === "error" ? "alert" : "status")}
      className={cn("flex items-start gap-3 rounded-(--radius-card) px-4 py-3", s.box, className)}
    >
      <span className={cn("mt-0.5 shrink-0", s.iconColor)}>{icon ?? <Icon name={s.icon} />}</span>
      <div className="min-w-0 flex-1 text-body-md text-ink">
        {title != null && <div className="mb-0.5 text-headline-md">{title}</div>}
        {children}
      </div>
      {actions != null && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
