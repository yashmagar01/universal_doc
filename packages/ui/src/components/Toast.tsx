import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { cn } from "../cn";

export type Toast = { id: number; text: string; tone: "info" | "success" | "error"; action?: { label: string; onClick: () => void } };

const ToastContext = createContext<(t: Omit<Toast, "id">) => void>(() => {});

export function useToast(): (t: Omit<Toast, "id">) => void {
  return useContext(ToastContext);
}

const toneIcon: Record<Toast["tone"], IconName> = { info: "info", success: "check_circle", error: "warning" };

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const next = useRef(1);

  const push = useCallback((t: Omit<Toast, "id">) => {
    const id = next.current++;
    setItems((old) => [...old, { ...t, id }]);
    if (t.tone !== "error") {
      setTimeout(() => setItems((old) => old.filter((i) => i.id !== id)), 4000);
    }
  }, []);
  const value = useMemo(() => push, [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live={items.some((i) => i.tone === "error") ? "assertive" : "polite"}
        className="fixed bottom-10 left-4 z-50 flex w-80 flex-col gap-2"
      >
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-2 rounded-(--radius-card) bg-card px-3 py-2 text-body-sm shadow-l3",
              t.tone === "error" && "text-error",
            )}
          >
            <Icon name={toneIcon[t.tone]} className={cn(t.tone === "error" && "text-error", t.tone === "success" && "text-success", t.tone === "info" && "text-brand")} />
            <span className="flex-1 text-ink">{t.text}</span>
            {t.action && (
              <button
                type="button"
                onClick={() => {
                  t.action?.onClick();
                  setItems((old) => old.filter((i) => i.id !== t.id));
                }}
                className="rounded-pill px-2 py-1 text-label-md text-brand hover:bg-brand-tint"
              >
                {t.action.label}
              </button>
            )}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
