import { Component, type ReactNode } from "react";

interface State {
  error: Error | null;
}

/** FR-ERR-*: Every screen is wrapped; failure shows honest error + Reload, never a blank page. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex min-h-dvh items-center justify-center bg-canvas">
        <div className="w-[400px] rounded-lg bg-card border border-border p-6 shadow-l1 text-center">
          <h1 className="text-headline-sm font-semibold text-secondary">Templix hit an unexpected error</h1>
          <p className="mt-2 text-sm text-ink-2">{String(this.state.error?.message ?? this.state.error)}</p>
          <button
            className="mt-4 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-white hover:bg-brand"
            onClick={() => location.reload()}
          >
            Reload Templix
          </button>
        </div>
      </div>
    );
  }
}
