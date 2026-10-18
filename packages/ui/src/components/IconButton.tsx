import { forwardRef, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { Tooltip } from "./Tooltip";
import { cn } from "../cn";

export const IconButton = forwardRef<
  HTMLButtonElement,
  {
    icon: IconName;
    label: string;
    onClick?: () => void;
    toggled?: boolean;
    active?: boolean;
    className?: string;
    tooltipSide?: "top" | "bottom";
    children?: ReactNode;
  }
>(function IconButton(
  { icon, label, onClick, toggled = false, active = false, className, tooltipSide = "bottom", children },
  ref,
) {
  return (
    <Tooltip content={label} side={tooltipSide}>
      <button
        ref={ref}
        type="button"
        onClick={onClick}
        aria-label={label}
        aria-pressed={toggled || undefined}
        className={cn(
          "inline-flex size-9 items-center justify-center rounded-full text-ink-2 transition-colors duration-150 select-none",
          "hover:bg-black/4 hover:text-ink",
          active ? "bg-brand-tint text-brand" : "bg-transparent",
          toggled && "text-brand",
          className,
        )}
      >
        {children ?? <Icon name={icon} fill={active} />}
      </button>
    </Tooltip>
  );
});
