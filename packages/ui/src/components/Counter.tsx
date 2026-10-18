import { cn } from "../cn";

export type CounterState = "ok" | "near" | "over";

export function counterState(value: number, max: number): CounterState {
  const ratio = value / max;
  if (ratio > 1) return "over";
  if (ratio >= 0.9) return "near";
  return "ok";
}

/** tabular counter, state derived from value/max — never colour alone (state word appended) */
export function Counter({ value, max, count = "chars" }: { value: number; max: number; count?: "chars" | "words" }) {
  const state = counterState(value, max);
  const stateWord = state === "ok" ? null : state === "near" ? "Near limit" : "Over";
  return (
    <span
      className={cn(
        "text-body-sm tabular-nums",
        state === "ok" && "text-ink-2",
        state === "near" && "text-warning",
        state === "over" && "font-semibold text-error",
      )}
    >
      {value} / {max} {count}
      {stateWord && <> — {stateWord}</>}
    </span>
  );
}
