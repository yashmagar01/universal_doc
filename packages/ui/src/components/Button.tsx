import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router";
import { cn } from "../cn";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "danger-solid" | "warning-solid";
export type ButtonSize = "sm" | "md" | "lg" | "xl";

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-7 px-3 text-xs",
  md: "h-8 px-4 text-body-md font-semibold",
  lg: "h-10 px-5 text-body-md font-semibold",
  xl: "h-12 px-8 text-body-lg font-semibold",
};

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-brand text-white hover:bg-brand-hover border border-transparent",
  secondary: "border border-brand text-brand hover:bg-brand-tint hover:border-[1.5px]",
  ghost: "text-ink-2 hover:text-ink hover:bg-black/4 border border-transparent",
  danger: "border border-error text-error bg-card hover:bg-error-bg",
  "danger-solid": "border border-transparent bg-error text-white hover:opacity-90",
  "warning-solid": "border border-transparent bg-warning text-white hover:opacity-90",
};

type Base = { variant?: ButtonVariant; size?: ButtonSize; loading?: boolean; leading?: ReactNode; trailing?: ReactNode; className?: string };

function content(loading: boolean, leading: ReactNode, trailing: ReactNode, children: React.ReactNode) {
  return (
    <>
      {loading ? (
        <span aria-hidden className="mr-1 inline-block size-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
      ) : (
        leading
      )}
      {children}
      {trailing}
    </>
  );
}

/** Renders a router <Link> when `to` is set (avoids link>wrapping>button nesting for a11y). */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  leading,
  trailing,
  className,
  children,
  disabled,
  to,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & Base & { to?: string }) {
  const cls = cn(
    "inline-flex items-center justify-center gap-2 rounded-pill whitespace-nowrap transition-colors duration-150 select-none",
    sizeClasses[size],
    variantClasses[variant],
    (disabled || loading) && "bg-ink-disabled text-card border-transparent cursor-not-allowed hover:bg-ink-disabled",
    loading && "bg-brand/60",
    className,
  );
  if (to != null && !disabled && !loading) {
    return (
      <Link to={to} className={cls} {...(rest as Record<string, unknown>)}>
        {content(loading, leading, trailing, children)}
      </Link>
    );
  }
  return (
    <button
      type="button"
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cls}
      {...rest}
    >
      {content(loading, leading, trailing, children)}
    </button>
  );
}
