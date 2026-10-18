import { forwardRef, type ReactNode } from "react";
import { Icon } from "./Icon";
import { cn } from "../cn";

const fieldBase =
  "w-full rounded-(--radius-input) border border-ink-2 bg-card px-3 text-body-md text-ink transition-colors duration-150 placeholder:text-ink-2";
const fieldHover = "hover:border-ink";
const fieldFocus = "focus:border-brand focus:shadow-[0_0_0_1px_var(--color-brand)] focus:outline-none";
const fieldError = "border-error";

export function Field({
  label,
  hint,
  error,
  counter,
  required,
  htmlFor,
  children,
  className,
}: {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  counter?: ReactNode;
  required?: boolean;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={htmlFor} className="text-label-md text-ink">
          {label}
          {required && <span className="ml-0.5 text-error">*</span>}
        </label>
        {counter}
      </div>
      {children}
      {error != null ? (
        <div className="flex items-center gap-1 text-body-sm text-error">
          <Icon name="warning" className="text-[14px]" />
          {error}
        </div>
      ) : (
        hint != null && <div className="text-body-sm text-ink-2">{hint}</div>
      )}
    </div>
  );
}

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }
>(function Input({ invalid = false, className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(fieldBase, fieldHover, fieldFocus, "h-9", invalid && fieldError, className)}
      {...rest}
    />
  );
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }
>(function Textarea({ invalid = false, className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(fieldBase, fieldHover, fieldFocus, "min-h-20 py-2", invalid && fieldError, className)}
      {...rest}
    />
  );
});

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean }
>(function Select({ invalid = false, className, children, ...rest }, ref) {
  return (
    <div className="relative">
      <select
        ref={ref}
        aria-invalid={invalid || undefined}
        className={cn(
          fieldBase,
          fieldHover,
          fieldFocus,
          "h-9 appearance-none pr-8",
          invalid && fieldError,
          className,
        )}
        {...rest}
      >
        {children}
      </select>
      <Icon
        name="expand_more"
        className="pointer-events-none absolute top-1/2 right-2 -translate-y-1/2 text-ink-2"
        label={undefined}
      />
    </div>
  );
});
