import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { Banner, Button, Card, Icon, Tag, TemplateCard } from "@templix/ui";
import { AppShell } from "./AppShell";
import { copy } from "../lib/copy";
import { EngineTile, GreetingHeader, PrivacyTile } from "./Home";
import { ensureSession, listTemplates, uploadPdf, type TemplateSummary } from "../lib/api";
import type { ProfileInfo, StatusBarContent } from "../lib/types";
import { useLiveStatus } from "../lib/useStatus";

/** No account exists in a local-first app; this is honest placeholder identity, not a person. */
const LIVE_USER: ProfileInfo = {
  name: "Local user",
  role: "This device",
  team: "Local workspace",
  orgChip: "Local workspace",
};

/** Live Home: templates come from GET /templates; upload queues the ingest job (FR-HOME-02/03). */
export function HomeLive() {
  const live = useLiveStatus();
  const status: StatusBarContent = {
    ram: live?.ram ?? "—",
    parser: live?.parser ?? "PDF Parser: connecting…",
    privacyMode: live?.privacyMode ?? "No telemetry",
    user: LIVE_USER,
  };
  return (
    <AppShell active="home" status={status}>
      <div className="space-y-5">
        <GreetingHeader />
        <div className="grid grid-cols-12 gap-5">
          <TemplatesTileLive />
          <PrivacyTile />
          <EngineTile />
        </div>
        <div className="grid grid-cols-12 gap-5">
          <QuickActionsTileLive />
          <Card
            className="col-span-12"
            title="System Diagnostics & Technical"
            action={<Tag tone="success">All Services Active</Tag>}
          >
            <Banner tone="info" icon={<Icon name="shield" />} title={copy.indicator.staysLocal}>
              <span className="text-sm text-ink-2">
                Local runtime: server running · parser loaded · renderer ready · storage local
              </span>
            </Banner>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

function TemplatesTileLive() {
  const [templates, setTemplates] = useState<TemplateSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    ensureSession()
      .then(listTemplates)
      .then((rows) => {
        if (alive) setTemplates(rows);
      })
      .catch((err: unknown) => {
        if (alive) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <Card
      className="col-span-12 min-[900px]:col-span-7"
      title="Templates & Analytics"
      footer={
        <span className="text-xs text-ink-2">
          {templates ? `${templates.length} templates · ` : ""}stored locally on this machine
        </span>
      }
    >
      {error && (
        <Banner tone="warning" title="Local server unreachable">
          <span className="text-sm text-ink-2">{error}</span>
        </Banner>
      )}
      {templates === null && !error && <p className="text-sm text-ink-2">Loading templates…</p>}
      {templates?.length === 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-border bg-surface-2 p-4">
          <Icon name="upload_file" className="text-ink-2" />
          <p className="text-sm text-ink-2">
            No templates yet — upload a reference PDF to create your first one.
          </p>
        </div>
      )}
      <div className="flex flex-wrap gap-4">
        {(templates ?? []).slice(0, 3).map((tpl) => (
          <Link
            key={tpl.id}
            to={`/templates/${tpl.id}/analysis`}
            className="flex-1 basis-[180px] min-w-[180px]"
          >
            <span className="sr-only">{tpl.name}</span>
            <TemplateCard
              name={tpl.name}
              meta={`${tpl.layerCount} layers extracted · ${tpl.pageCount} pages · ${formatDate(tpl.updatedAt)}`}
              status={tpl.status === "needs-review" ? "needs-review" : "ready"}
              kindTag="PDF"
            />
          </Link>
        ))}
      </div>
    </Card>
  );
}

function QuickActionsTileLive() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allowManyPages, setAllowManyPages] = useState(false);

  async function onPick(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const accepted = await uploadPdf(file, allowManyPages);
      void navigate(`/templates/${accepted.templateId}/analysis`, {
        state: { jobId: accepted.jobId, fileName: file.name },
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <Card className="col-span-12" title="Quick Actions">
      <input
        ref={inputRef}
        data-qa="upload-input"
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(e) => void onPick(e.target.files?.[0])}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          size="sm"
          leading={<Icon name="upload_file" className="text-[16px]" />}
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          {busy ? "Uploading…" : "Upload reference PDF"}
        </Button>
        <Button
          to="/templates"
          variant="ghost"
          size="sm"
          leading={<Icon name="add" className="text-[16px]" />}
        >
          Start from template
        </Button>
        <Button variant="ghost" size="sm" disabled leading={<Icon name="doc_edit" className="text-[16px]" />}>
          New blank template (soon)
        </Button>
        <Button variant="ghost" size="sm" disabled leading={<Icon name="smart_toy" className="text-[16px]" />}>
          New from AI prompt (soon)
        </Button>
      </div>
      <label className="mt-3 flex w-fit items-center gap-2 text-xs text-ink-2">
        <input
          type="checkbox"
          data-qa="allow-many-pages"
          checked={allowManyPages}
          disabled={busy}
          onChange={(e) => setAllowManyPages(e.target.checked)}
        />
        Allow PDFs with more than 50 pages
      </label>
      {error && (
        <p className="mt-3 text-sm text-error" role="alert">
          {error}
        </p>
      )}
      <p className="mt-3 text-xs text-ink-2">
        Ingestion runs locally: parse, layer detection, review queue — no upload leaves this machine.
      </p>
    </Card>
  );
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleDateString();
}
