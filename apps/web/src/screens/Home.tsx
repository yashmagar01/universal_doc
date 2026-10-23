import { useState } from "react";
import { Link } from "react-router";
import { Banner, Button, Card, FileChip, IconButton, Icon, Tag, TemplateCard } from "@templix/ui";
import { AppShell } from "./AppShell";
import { copy } from "../lib/copy";
import type { ProfileInfo } from "../lib/types";
import { fixtureCounts, fixtureDocuments, fixtureProvider, fixtureStatus, fixtureTemplates } from "../fixtures/demo";

export function HomePage() {
  const [showTech, setShowTech] = useState(false);
  return (
    <AppShell active="home" status={fixtureStatus}>
      <div className="space-y-5">
        <GreetingHeader user={fixtureStatus.user} />
        <div className="grid grid-cols-12 gap-5">
          <TemplatesTile />
          <PrivacyTile />
          <EngineTile />
        </div>
        <div className="grid grid-cols-12 gap-5">
          <RecentWorkTile />
          <QuickActionsTile />
          <Card className="col-span-12" title="System Diagnostics & Technical" action={
            <div className="flex items-center gap-1">
              <Tag tone="success">All Services Active</Tag>
              <IconButton icon="settings" label="System Settings" />
              <IconButton icon={showTech ? "expand_less" : "expand_more"} label={showTech ? "Hide engine status" : "Show engine status"} onClick={() => setShowTech((v) => !v)} />
            </div>
          }>
            {showTech ? (
              <Banner tone="info" icon={<Icon name="shield" />} title={copy.indicator.staysLocal}>
                <span className="text-sm text-ink-2">
                  Local runtime: server running · parser loaded · renderer ready · storage local ({fixtureCounts.storageUsed})
                </span>
              </Banner>
            ) : (
              <p className="text-sm text-ink-2">Expand for engine status.</p>
            )}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

export function GreetingHeader({ user }: { user?: ProfileInfo }) {
  const parts = user?.name.split(" ") ?? [];
  const initials = ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex shrink-0 items-center gap-3">
        <span className="grid size-12 place-items-center rounded-full bg-primary text-lg font-semibold text-white">
          {user ? initials : <Icon name="manage_accounts" />}
        </span>
        <div>
          <h1 className="text-headline-md font-semibold text-secondary">
            {user ? `Welcome back, ${parts[0] ?? user.name}` : "Welcome back"}
          </h1>
          <p className="text-sm text-ink-2">
            {user ? `${user.role} · ${user.team}` : "Local workspace · your files stay on this machine"}
          </p>
        </div>
      </div>
      <span
        data-qa="local-app-badge"
        title={copy.badge.localTooltip}
        className="mt-1 inline-flex shrink-0 items-center gap-1 rounded-md bg-blue-50 px-2 py-1 text-xs font-bold tracking-wide text-brand ring-1 ring-brand/20 whitespace-nowrap"
      >
        <Icon name="shield" className="text-[14px]" />
        {copy.badge.local}
      </span>
    </div>
  );
}

function TemplatesTile() {
  return (
    <Card
      className="col-span-12 min-[900px]:col-span-7"
      title="Templates & Analytics"
      action={<Button to="/templates" variant="ghost" size="sm">View all</Button>}
      footer={<span className="text-xs text-ink-2">Lifetime: {fixtureCounts.documentsCreated} documents created · {fixtureCounts.templatesManaged} templates · {fixtureCounts.storageUsed} storage</span>}
    >
      <div className="flex flex-wrap gap-4">
        {fixtureTemplates.map((tpl) => (
          <Link key={tpl.id} to={`/templates/${tpl.id}/analysis`} className="flex-1 basis-[180px] min-w-[180px]">
            <span className="sr-only">{tpl.name}</span>
            <TemplateCard
              name={tpl.name}
              meta={`${tpl.layers} layers extracted · ${tpl.pages} pages · Last used ${tpl.lastUsed}`}
              status={tpl.status}
              kindTag={tpl.kind}
            />
          </Link>
        ))}
      </div>
    </Card>
  );
}

export function PrivacyTile() {
  const p = fixtureProvider;
  const text = p.connected
    ? copy.privacy.cardProvider(p.label)
    : copy.privacy.cardNone;
  return (
    <Card
      className="col-span-12 min-[900px]:col-span-5"
      title="Privacy & Data Policy"
      titleIcon={<span className="grid size-7 place-items-center rounded-full bg-brand-tint text-brand"><Icon name="shield" /></span>}
    >
      <p className="text-sm font-semibold text-secondary">{text.title}</p>
      <p className="mt-1 text-sm text-ink-2">{text.body}</p>
    </Card>
  );
}

export function EngineTile() {
  const connected = fixtureProvider.connected;
  return (
    <Card
      className="col-span-12 min-[900px]:col-span-4"
      title="Engine Studio"
      action={<Button to="/settings" variant="ghost" size="sm">Manage</Button>}
    >
      {connected ? (
        <div className="flex items-center gap-3 rounded-lg bg-surface-2 p-3">
          <span className="grid size-9 place-items-center rounded-full bg-brand text-white"><Icon name="smart_toy" /></span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-secondary">Templix Assistant</p>
            <p className="text-xs text-ink-2">AI Assist enabled for supported templates</p>
          </div>
          <Tag tone="success">{copy.home.aiOn}</Tag>
        </div>
      ) : (
        <div className="flex gap-3 rounded-lg border border-dashed border-border bg-surface-2 p-3">
          <Icon name="smart_toy" className="mt-0.5 text-ink-2" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-secondary">{copy.home.engineNone}</p>
            <p className="text-xs text-ink-2">Templates without AI still support full manual editing and export.</p>
          </div>
        </div>
      )}
      <FileChip className="mt-3" name="Engine Add-ons: PDF viewer (local)" />
    </Card>
  );
}

export function RecentWorkTile() {
  return (
    <Card
      className="col-span-12 min-[900px]:col-span-7"
      title="Recent Work"
      action={<Button to="/documents" variant="ghost" size="sm">View all documents</Button>}
    >
      <div className="space-y-2">
        {fixtureDocuments.map((d) => {
          const to =
            d.status === "in-progress-ai" ? `/documents/${d.id}/ai` :
            d.status === "in-progress-manual" ? `/documents/${d.id}/manual` :
            undefined;
          const row = (
            <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-2 px-3 py-2 transition-colors hover:border-brand hover:bg-brand-tint/40">
              <Icon name={d.exported ? "check_circle" : d.status === "in-progress-ai" ? "auto_awesome" : "edit"} className={d.exported ? "text-success" : "text-brand"} />
              <p className="min-w-0 flex-1 truncate text-sm font-medium text-secondary">{d.title}</p>
              <span className="shrink-0 text-xs text-ink-2 whitespace-nowrap">{d.updated}</span>
              <Tag tone={d.exported ? "success" : d.status === "in-progress-ai" ? "brand" : "info"}>
                {d.exported ? "Exported" : d.status === "in-progress-ai" ? "AI Assisted" : "Manual Edit"}
              </Tag>
            </div>
          );
          return to ? (
            <Link key={d.id} to={to} className="block">{row}</Link>
          ) : (
            <div key={d.id} data-qa="doc-row-done">{row}</div>
          );
        })}
      </div>
    </Card>
  );
}

function QuickActionsTile() {
  return (
    <Card className="col-span-12 min-[900px]:col-span-5" title="Quick Actions">
      <div className="flex flex-wrap gap-2">
        <Button to="/templates" variant="secondary" size="sm" leading={<Icon name="add" className="text-[16px]" />}>Start from template</Button>
        <Button variant="ghost" size="sm" leading={<Icon name="upload_file" className="text-[16px]" />}>Upload reference PDF</Button>
        <Button variant="ghost" size="sm" leading={<Icon name="doc_edit" className="text-[16px]" />}>New blank template</Button>
        <Button variant="ghost" size="sm" leading={<Icon name="smart_toy" className="text-[16px]" />}>New from AI prompt</Button>
      </div>
    </Card>
  );
}
