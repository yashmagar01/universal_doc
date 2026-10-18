import type { ReactNode } from "react";
import * as Radix from "radix-ui";
import { cn } from "../cn";

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  maxWidth = 480,
  children,
  footer,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  maxWidth?: number | string;
  children?: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <Radix.Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Radix.Dialog.Portal>
        <Radix.Dialog.Overlay className="fixed inset-0 z-50 bg-(--color-scrim)" />
        <Radix.Dialog.Content
          style={{ maxWidth }}
          className={cn(
            "fixed top-1/2 left-1/2 z-50 max-h-[85dvh] w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-(--radius-card) bg-card p-5 shadow-l3",
            "data-[state=open]:animate-in data-[state=open]:fade-in data-[state=open]:zoom-in-95",
          )}
        >
          <Radix.Dialog.Title className="mb-1 text-headline-lg">{title}</Radix.Dialog.Title>
          {description != null && (
            <Radix.Dialog.Description className="text-body-md text-ink-2">{description}</Radix.Dialog.Description>
          )}
          {children != null && <div className="mt-4">{children}</div>}
          {footer != null && <div className="mt-5 flex justify-end gap-2">{footer}</div>}
        </Radix.Dialog.Content>
      </Radix.Dialog.Portal>
    </Radix.Dialog.Root>
  );
}
