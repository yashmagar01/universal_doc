import { Link, useParams } from "react-router";
import {
  Banner,
  Button,
  Card,
  Field,
  Icon,
  Input,
  StatusPill,
  Tag,
  Switch,
} from "@templix/ui";
import { AppShell } from "./AppShell";
import { copy } from "../lib/copy";
import { fixtureProvider, fixtureSettings, fixtureStatus } from "../fixtures/demo";

const NAV_SECTIONS = [
  { key: "ai-models", label: "AI Models & Providers" },
  { key: "local-runtime", label: "Local Runtime" },
  { key: "data", label: "Data & Storage" },
  { key: "privacy", label: "Privacy & Telemetry" },
] as const;

type SectionKey = (typeof NAV_SECTIONS)[number]["key"];

export function SettingsScreen() {
  const { section } = useParams();
  const active: SectionKey = (NAV_SECTIONS.find((s) => s.key === section)?.key ?? "ai-models") as SectionKey;

  return (
    <AppShell active={active === "privacy" ? "privacy" : active === "ai-models" ? "models" : "home"} status={fixtureStatus}>
      <div className="grid grid-cols-12 gap-6">
        <nav aria-label="Settings sections" data-qa="settings-nav" className="col-span-12 min-[900px]:col-span-3">
          <ul className="space-y-1">
            {NAV_SECTIONS.map((s) => (
              <li key={s.key}>
                <Link
                  to={`/settings/${s.key}`}
                  aria-current={active === s.key ? "page" : undefined}
                  className={`block rounded-md px-3 py-2 text-sm font-medium ${
                    active === s.key ? "bg-brand-tint text-brand" : "text-ink-2 hover:bg-black/4"
                  }`}
                >
                  {s.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="col-span-12 min-[900px]:col-span-9 space-y-5">
          {active === "ai-models" && <AiModelsSection />}
          {active === "local-runtime" && <LocalRuntimeSection />}
          {active === "data" && <DataSection />}
          {active === "privacy" && <PrivacySection />}
        </div>
      </div>
    </AppShell>
  );
}

function AiModelsSection() {
  const configured = fixtureSettings.configuredCount;
  return (
    <>
      <Card
        title="AI Models & Providers"
        action={<Tag tone={configured > 0 ? "success" : "neutral"}>{configured} configured</Tag>}
      >
        <p className="text-sm text-ink-2">{copy.settings.keyNote}</p>
        <p className="mt-2 text-sm text-ink-2">{copy.settings.dataBoundary}</p>
      </Card>

      <div className="space-y-3">
        {fixtureSettings.engines.map((e) => (
          <Card key={e.id}>
            <div className="flex flex-wrap items-center gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-full bg-brand-tint text-brand">
                <Icon name={e.id === "ollama" ? "memory" : "smart_toy"} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-ink">{e.name}</p>
                  {e.comingSoon ? <Tag tone="neutral">{e.tag}</Tag> : <Tag tone="info">{e.tag}</Tag>}
                  {e.configured && <StatusPill tone="success" icon="check_circle">Configured</StatusPill>}
                </div>
                <p className="text-xs text-ink-2">{e.id === "ollama" ? copy.settings.ollama : e.desc}</p>
              </div>
              {e.comingSoon ? (
                <Tag tone="neutral">Coming soon</Tag>
              ) : (
                <Button variant={e.configured ? "secondary" : "primary"} size="sm" to={`/settings/ai-models`}>
                  {e.configured ? "Update key" : "Add API key"}
                </Button>
              )}
            </div>
            {e.configured && (
              <div className="mt-3 grid gap-3 border-t border-divider pt-3 min-[700px]:grid-cols-2">
                <Field label="API key" htmlFor={`key-${e.id}`} hint="Stored in this computer's keychain. Write-only here.">
                  <Input id={`key-${e.id}`} type="password" value="••••••••••••3f2a" readOnly />
                </Field>
                <Field label="Model" htmlFor={`model-${e.id}`} hint="Comma-separated, first is default">
                  <Input id={`model-${e.id}`} defaultValue="claude-sonnet-4-5, claude-haiku-4-5" />
                </Field>
              </div>
            )}
          </Card>
        ))}
      </div>
    </>
  );
}

function LocalRuntimeSection() {
  return (
    <>
      <Card title="Local Runtime">
        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-2"><Icon name="check_circle" className="text-success" />Server: {fixtureSettings.localRuntime.server}</li>
          <li className="flex items-center gap-2"><Icon name="check_circle" className="text-success" />Parser: loaded (v0)</li>
          <li className="flex items-center gap-2"><Icon name="check_circle" className="text-success" />Renderer: ready</li>
          <li className="flex items-center gap-2"><Icon name="check_circle" className="text-success" />Cache: {fixtureSettings.localRuntime.cache}</li>
        </ul>
      </Card>
      <Banner tone="info" title="Templix does not run a background service">
        <span className="text-sm">The local runtime starts with the app and stops when it closes.</span>
      </Banner>
    </>
  );
}

function DataSection() {
  return (
    <>
      <Card title="Data & Storage" action={<Tag tone="neutral">{fixtureSettings.localRuntime.cache} used</Tag>}>
        <ul className="space-y-2 text-sm text-ink-2">
          <li>Templates, documents and settings are stored on this computer.</li>
          <li>Export your workspace as a portable archive.</li>
          <li>Import restores templates and preferences (keys are not included).</li>
        </ul>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" leading={<Icon name="download" className="text-[16px]" />}>Export workspace</Button>
          <Button variant="secondary" size="sm" leading={<Icon name="upload_file" className="text-[16px]" />}>Import workspace</Button>
          <Button variant="danger" size="sm" leading={<Icon name="close" className="text-[16px]" />}>Delete all local data</Button>
        </div>
      </Card>
      <Card title="Activity & Privacy Log">
        <ul className="space-y-1 text-sm text-ink-2">
          <li className="flex items-center gap-2"><span className="text-ink-2">Today 10:42</span> — Analysis ran locally (2 pages).</li>
          <li className="flex items-center gap-2"><span className="text-ink-2">Today 10:44</span> — Manual edit opened.</li>
        </ul>
        <p className="mt-2 text-xs text-ink-2">Provider calls appear here with section, model and timestamp when AI Assist is used.</p>
      </Card>
    </>
  );
}

function PrivacySection() {
  return (
    <>
      <Card title="Privacy & Telemetry">
        <ul className="space-y-3 text-sm">
          <li className="flex items-center justify-between gap-3">
            <span>
              <span className="block font-medium text-ink">Telemetry</span>
              <span className="text-xs text-ink-2">Templix never sends usage data anywhere.</span>
            </span>
            <Switch checked={false} onCheckedChange={() => {}} label="Telemetry (always off)" />
          </li>
          <li className="flex items-center justify-between gap-3">
            <span>
              <span className="block font-medium text-ink">Crash reports</span>
              <span className="text-xs text-ink-2">Saved to a local file you can review and delete.</span>
            </span>
            <Switch checked onCheckedChange={() => {}} label="Local crash reports" />
          </li>
          <li className="flex items-center justify-between gap-3">
            <span>
              <span className="block font-medium text-ink">AI privacy indicators</span>
              <span className="text-xs text-ink-2">Show what is sent to providers before each call.</span>
            </span>
            <Switch checked onCheckedChange={() => {}} label="AI privacy indicators" />
          </li>
        </ul>
      </Card>
      <Card title="Default privacy state">
        <p className="text-sm text-ink-2">
          {fixtureProvider.connected
            ? copy.privacy.cardProvider(fixtureProvider.label).body
            : copy.privacy.cardNone.body}
        </p>
        <p className="mt-2 text-sm text-ink-2">
          Provider calls are always opt-in and reversible. {copy.settings.keyNote}
        </p>
      </Card>
    </>
  );
}
