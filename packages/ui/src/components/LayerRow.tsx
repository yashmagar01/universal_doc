import { Icon } from "./Icon";
import { Switch } from "./Switch";
import { Tag } from "./Tag";
import { Tooltip } from "./Tooltip";
import { cn } from "../cn";
import type { ReactNode } from "react";

export type LayerRowState =
  | { kind: "editable-outlined" }
  | { kind: "slot"; slotLabel: string }
  | { kind: "fixed" }
  | { kind: "review"; reason: string };

export function LayerRow({
  name,
  roleLabel,
  state,
  selected = false,
  onToggleEditable,
  editable = false,
  locked = false,
  indent = 0,
  inspectAction,
  className,
}: {
  name: string;
  roleLabel: string;
  state: LayerRowState;
  selected?: boolean;
  onToggleEditable?: (v: boolean) => void;
  editable?: boolean;
  locked?: boolean;
  indent?: number;
  inspectAction?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex h-9 items-center gap-2 rounded-(--radius-input) px-2 select-none",
        selected && "border-l-2 border-brand bg-brand-tint pl-1.5",
        state.kind === "review" && "border-l-2 border-warning bg-warning-bg",
        className,
      )}
      style={{ marginLeft: indent * 16 }}
      data-qa="layer-row"
      data-state={state.kind}
    >
      <Tooltip content="Toggle visibility">
        <Icon name="visibility" className="text-ink-2" />
      </Tooltip>
      <Tooltip content={locked ? "Locked layers cannot be moved or deleted" : "Layer lock"}>
        <Icon name={locked ? "lock" : "lock_open"} className="text-ink-2" />
      </Tooltip>
      <Tooltip content={`${roleLabel}: ${name}`}>
        <span className="min-w-0 flex-1 truncate text-body-md text-ink">{name}</span>
      </Tooltip>
      {state.kind === "editable-outlined" && onToggleEditable && (
        <span className="flex items-center gap-1.5 text-label-sm text-ink-2">
          Edit
          <Switch checked={editable} onCheckedChange={(v) => onToggleEditable(v)} label={`Editable: ${name}`} />
        </span>
      )}
      {state.kind === "slot" && <Tag tone="info">Slot</Tag>}
      {state.kind === "fixed" && <span className="text-label-sm text-ink-2">Fixed</span>}
      {state.kind === "review" && (
        <>
          <span className="flex min-w-0 flex-1 items-center gap-1 text-body-sm text-warning">
            <Icon name="warning" className="text-[14px]" />
            <span className="truncate">{state.reason}</span>
          </span>
          {inspectAction ?? (
            <a href="#inspect" className="text-label-md text-warning underline">
              Inspect
            </a>
          )}
        </>
      )}
    </div>
  );
}
