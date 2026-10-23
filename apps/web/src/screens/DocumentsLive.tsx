import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { Banner, Button, Card, Icon, Tag } from "@templix/ui";
import { AppShell } from "./AppShell";
import {
  ensureSession,
  listDocuments,
  listTemplates,
  type DocumentSummary,
  type TemplateSummary,
} from "../lib/api";
import type { ProfileInfo, StatusBarContent } from "../lib/types";
import { useLiveStatus } from "../lib/useStatus";

const LIVE_USER: ProfileInfo = {
  name: "Local user",
  role: "This device",
  team: "Local workspace",
  orgChip: "Local workspace",
};

/** Live document list: reopen any draft in the manual editor. */
export function DocumentsLive() {
  const live = useLiveStatus();
  const status: StatusBarContent = {
    ram: live?.ram ?? "—",
    parser: live?.parser ?? "PDF Parser: connecting…",
    privacyMode: live?.privacyMode ?? "No telemetry",
    user: LIVE_USER,
  };
  const [documents, setDocuments] = useState<DocumentSummary[] | null>(null);
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    ensureSession()
      .then(() => Promise.all([listDocuments(), listTemplates()]))
      .then(([documentRows, templateRows]) => {
        if (!alive) return;
        setDocuments(documentRows);
        setTemplates(templateRows);
      })
      .catch((err: unknown) => {
        if (alive) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      alive = false;
    };
  }, []);

  const templateNames = useMemo(
    () => new Map(templates.map((template) => [template.id, template.name])),
    [templates],
  );

  return (
    <AppShell active="documents" status={status}>
      <Card
        title="Documents"
        footer={
          <span className="text-xs text-ink-2">
            {documents ? `${documents.length} drafts · ` : ""}stored locally on this machine
          </span>
        }
      >
        {error && (
          <Banner tone="warning" title="Local server unreachable">
            <span className="text-sm text-ink-2">{error}</span>
          </Banner>
        )}
        {documents === null && !error && <p className="text-sm text-ink-2">Loading documents…</p>}
        {documents?.length === 0 && (
          <div className="flex items-center gap-3 rounded-lg border border-dashed border-border bg-surface-2 p-4">
            <Icon name="description" className="text-ink-2" />
            <p className="text-sm text-ink-2">
              No drafts yet — open a template, then choose <strong>Edit content</strong>.
            </p>
            <Button to="/" variant="secondary" size="sm" className="ml-auto">
              Go to templates
            </Button>
          </div>
        )}
        {documents && documents.length > 0 && (
          <ul className="divide-y divide-border">
            {documents.map((document) => (
              <li key={document.id} className="flex items-center gap-3 py-3">
                <Icon name="description" className="shrink-0 text-ink-2" />
                <div className="min-w-0 flex-1">
                  <Link
                    to={`/documents/${document.id}/manual`}
                    className="block truncate text-sm font-medium text-ink hover:text-brand"
                  >
                    {templateNames.get(document.templateId) ?? "Untitled template"}
                  </Link>
                  <p className="text-xs text-ink-2">
                    Template v{document.templateVersion} · updated {formatDate(document.updatedAt)}
                  </p>
                </div>
                <Tag tone={document.status === "final" ? "success" : "neutral"}>
                  {document.status}
                </Tag>
                <Button to={`/documents/${document.id}/manual`} variant="secondary" size="sm">
                  Open
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleDateString();
}
