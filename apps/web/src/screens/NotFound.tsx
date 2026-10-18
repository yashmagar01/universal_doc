import { Button, TopBar } from "@templix/ui";

export function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <TopBar active="home" query="" onQueryChange={() => {}} userName="" userRole="" />
      <main className="mx-auto flex w-full max-w-[1128px] flex-1 items-center justify-center" data-qa="main-content">
        <div className="max-w-[400px] rounded-lg border border-border bg-card p-6 text-center shadow-l1">
          <h1 className="text-headline-sm font-semibold text-ink">Page not found</h1>
          <p className="mt-2 text-sm text-ink-2">This address doesn't match anything in Templix.</p>
          <Button to="/" variant="primary" className="mt-4">Back to Home</Button>
        </div>
      </main>
    </div>
  );
}
