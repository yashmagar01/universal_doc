import { forwardRef } from "react";
import * as Radix from "radix-ui";
import { cn } from "../cn";

export const Switch = forwardRef<
  HTMLButtonElement,
  { checked: boolean; onCheckedChange: (v: boolean) => void; label: string; className?: string }
>(function Switch({ checked, onCheckedChange, label, className: _className }, ref) {
  return (
    <Radix.Switch.Root
      ref={ref}
      checked={checked}
      onCheckedChange={onCheckedChange}
      role="switch"
      aria-label={label}
      className={cn(
        "inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-pill transition-colors duration-150",
        checked ? "bg-brand" : "bg-border-strong",
      )}
    >
      <Radix.Switch.Thumb
        className={cn(
          "block size-4 translate-x-0.5 rounded-full bg-card shadow transition-transform duration-150",
          "data-[state=checked]:translate-x-[18px]",
        )}
      />
    </Radix.Switch.Root>
  );
});

export const Checkbox = forwardRef<
  HTMLInputElement,
  { checked?: boolean; onCheckedChange?: (v: boolean) => void; label: React.ReactNode; className?: string }
>(function Checkbox({ checked, onCheckedChange, label, className, ...rest }, ref) {
  return (
    <label className={cn("inline-flex cursor-pointer items-center gap-2 text-body-md text-ink", className)}>
      <input
        ref={ref}
        type="checkbox"
        checked={checked}
        onChange={(e) => onCheckedChange?.(e.target.checked)}
        className="size-4.5 appearance-none rounded-[4px] border-[1.5px] border-ink-2 bg-card transition-colors duration-150 checked:border-brand checked:bg-brand checked:bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z%22/></svg>')] checked:bg-center checked:bg-[length:14px] checked:bg-no-repeat"
        {...rest}
      />
      {label}
    </label>
  );
});

export const Radio = forwardRef<
  HTMLInputElement,
  { checked: boolean; onChange?: () => void; label: React.ReactNode; className?: string; name: string }
>(function Radio({ checked, onChange, label, className, name, ...rest }, ref) {
  return (
    <label className={cn("inline-flex cursor-pointer items-center gap-2 text-body-md text-ink", className)}>
      <input
        ref={ref}
        type="radio"
        name={name}
        checked={checked}
        onChange={onChange}
        className="size-4.5 appearance-none rounded-full border-[1.5px] border-ink-2 bg-card transition-colors duration-150 checked:border-[6px] checked:border-brand"
        {...rest}
      />
      {label}
    </label>
  );
});
