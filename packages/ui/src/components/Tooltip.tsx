import { forwardRef, type ReactNode } from "react";
import * as Radix from "radix-ui";
import { cn } from "../cn";

export const TooltipProvider = Radix.Tooltip.Provider;

export const Tooltip = forwardRef<
  HTMLDivElement,
  { content: ReactNode; side?: "top" | "right" | "bottom" | "left"; children: ReactNode; className?: string }
>(function Tooltip({ content, side = "top", children, className }, ref) {
  return (
    <Radix.Tooltip.Root delayDuration={300}>
      <Radix.Tooltip.Trigger asChild>{children}</Radix.Tooltip.Trigger>
      <Radix.Tooltip.Portal>
        <Radix.Tooltip.Content
          ref={ref}
          side={side}
          sideOffset={6}
          className={cn(
            "z-50 rounded-(--radius-input) bg-ink px-2 py-1 text-label-sm text-card shadow-l3 animate-in fade-in duration-150",
            className,
          )}
        >
          {content}
        </Radix.Tooltip.Content>
      </Radix.Tooltip.Portal>
    </Radix.Tooltip.Root>
  );
});
