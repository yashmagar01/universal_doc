import type { ReactNode } from "react";
import * as Radix from "radix-ui";
import { cn } from "../cn";

/**
 * Controlled tab shell. Panels are rendered here so Radix wires aria-controls properly.
 * `icon`/`badge` are optional per tab.
 */
export function Tabs<K extends string>({
  tabs,
  value,
  onValueChange,
  panels,
  className,
}: {
  tabs: { key: K; label: string; icon?: ReactNode; badge?: ReactNode }[];
  value: K;
  onValueChange: (k: K) => void;
  panels?: Partial<Record<K, ReactNode>>;
  className?: string;
}) {
  return (
    <Radix.Tabs.Root value={value} onValueChange={(v) => onValueChange(v as K)}>
      <Radix.Tabs.List className={cn("flex items-center justify-between gap-1 border-b border-divider", className)}>
        {tabs.map((t) => (
          <Radix.Tabs.Trigger
            key={t.key}
            value={t.key}
            data-qa={`tab-${t.key}`}
            className={cn(
              "flex h-10 items-center gap-1.5 border-b-2 border-transparent px-3 text-label-lg text-ink-2 transition-colors duration-150 select-none",
              "hover:text-ink data-[state=active]:border-brand data-[state=active]:text-ink",
            )}
          >
            {t.icon}
            {t.label}
            {t.badge}
          </Radix.Tabs.Trigger>
        ))}
      </Radix.Tabs.List>
      {panels != null &&
        tabs.map((t) => (
          <Radix.Tabs.Content key={t.key} value={t.key} data-qa={`tabpanel-${t.key}`}>
            {panels[t.key]}
          </Radix.Tabs.Content>
        ))}
    </Radix.Tabs.Root>
  );
}
