import { StatusBar, TopBar, type TopNavKey } from "@templix/ui";
import { useState } from "react";
import { APP_VERSION } from "../lib/version";
import type { StatusBarContent } from "../lib/types";

/** Shared app-shell scaffold: 56-px TopBar + 32-px StatusBar + max-w-1128 content column. */
export function AppShell({
  active,
  status,
  children,
}: {
  active: TopNavKey;
  status: StatusBarContent;
  children: React.ReactNode;
}) {
  const [q, setQ] = useState("");
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <TopBar active={active} query={q} onQueryChange={setQ} userName={status.user.name} userRole={status.user.role} />
      <main className="mx-auto w-full max-w-[1128px] flex-1 px-6 py-6" data-qa="main-content">{children}</main>
      <StatusBar
        left={{ engine: "Engine ready", detail: status.privacyMode, ram: status.ram, parser: status.parser }}
        privacyMode={status.privacyMode}
        version={APP_VERSION}
      />
    </div>
  );
}
