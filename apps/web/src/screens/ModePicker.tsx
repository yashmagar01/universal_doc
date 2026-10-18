import { useState } from "react";
import { Link, useParams } from "react-router";
import { Button, Card, FileChip, Icon, StatusBar, Tag, WorkspaceTopBar, type IconName } from "@templix/ui";
import { APP_VERSION } from "../lib/version";
import { copy } from "../lib/copy";
import { fixtureMode, fixtureStatus } from "../fixtures/demo";

export function ModeScreen() {
  const { templateId } = useParams();
  const m = fixtureMode;
  const [mode, setMode] = useState<"manual" | "ai" | null>(null);
  const providerOn = m.provider.connected;

  if (templateId !== m.templateId) {
    return <UnknownTemplate />;
  }

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={<Link to={`/templates/${m.templateId}/analysis`} aria-label="Back to analysis" className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4"><Icon name="arrow_back" /></Link>}
        file={m.fileName}
        fileMeta={`${m.pages} pages · ${m.layers} layers`}
        status={<Tag tone="info">Step 2 of 3 · Choose mode</Tag>}
        actions={<span className="hidden text-xs text-ink-2 min-[1100px]:inline">Analysis ran locally · ready</span>}
      />

      <main className="mx-auto w-full max-w-[840px] flex-1 px-6 py-8" data-qa="main-content">
        <h1 className="text-headline-lg font-semibold text-ink">How do you want to edit?</h1>
        <p className="mt-1 text-body-md text-ink-2">
          Both modes use the template you just analysed. You can switch later.
        </p>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          {/* Manual */}
          <ModeCard
            selected={mode === "manual"}
            onSelect={() => setMode("manual")}
            icon="edit"
            title="Manual Edit"
            description={copy.privacy.modeManual}
            bullets={[
              "Fill slots section by section",
              "Live counters and rule checks",
              "Runs entirely on this computer",
            ]}
            cta={mode === "manual" ? "Continue" : "Choose Manual"}
          />

          {/* AI */}
          <ModeCard
            selected={mode === "ai"}
            onSelect={providerOn ? () => setMode("ai") : undefined}
            icon="auto_awesome"
            title="AI Assist"
            description={providerOn ? copy.privacy.modeAi(m.provider.label) : copy.home.engineNone}
            bullets={
              providerOn
                ? ["Drafts from your prompt", "You review every change", copy.ai.protection]
                : ["Drafts from your prompt", "You review every change", "Add an API key in Settings to enable"]
            }
            disabled={!providerOn}
            cta={providerOn ? (mode === "ai" ? "Continue" : "Choose AI Assist") : "Add an API key"}
            ctaTo={providerOn ? undefined : "/settings"}
          />
        </div>

        <div className="mt-6 flex items-center justify-between rounded-card border border-border bg-card px-4 py-3 shadow-l1">
          <FileChip name={m.fileName} meta={`${m.pages} pages`} />
          {mode === null ? (
            <Button variant="primary" disabled>Pick a mode to continue</Button>
          ) : (
            <Button
              to={mode === "ai" ? "/documents/d_march/ai" : "/documents/d_march/manual"}
              variant="primary"
              trailing={<Icon name="arrow_forward" className="text-[16px]" />}
            >
              Open editor
            </Button>
          )}
        </div>
      </main>

      <StatusBar
        left={{ engine: "Engine ready", ram: "—", parser: fixtureStatus.parser }}
        privacyMode={fixtureStatus.privacyMode}
        version={APP_VERSION}
      />
    </div>
  );
}

function ModeCard({
  icon,
  title,
  description,
  bullets,
  cta,
  ctaTo,
  selected,
  onSelect,
  disabled = false,
}: {
  icon: IconName;
  title: string;
  description: string;
  bullets: string[];
  cta: string;
  ctaTo?: string;
  selected: boolean;
  onSelect?: () => void;
  disabled?: boolean;
}) {
  return (
    <Card
      className={`transition-shadow ${selected ? "ring-2 ring-brand" : ""}`}
      title={
        <span className="flex items-center gap-2">
          <span className="grid size-8 place-items-center rounded-full bg-brand-tint text-brand">
            <Icon name={icon} />
          </span>
          {title}
        </span>
      }
      action={selected ? <Tag tone="brand">Selected</Tag> : disabled ? <Tag tone="neutral">Setup needed</Tag> : undefined}
      footer={
        <div className="flex w-full justify-end">
          {ctaTo != null ? (
            <Button to={ctaTo} variant={disabled ? "secondary" : "primary"} size="sm">{cta}</Button>
          ) : (
            <Button
              variant={disabled ? "secondary" : "primary"}
              size="sm"
              disabled={disabled}
              onClick={onSelect}
            >
              {cta}
            </Button>
          )}
        </div>
      }
    >
      <p className="text-sm text-ink-2">{description}</p>
      <ul className="mt-3 space-y-1.5">
        {bullets.map((b) => (
          <li key={b} className="flex items-start gap-2 text-sm text-ink">
            <Icon name={disabled ? "info" : "check_circle"} className={`mt-0.5 shrink-0 text-[16px] ${disabled ? "text-ink-2" : "text-success"}`} />
            {b}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function UnknownTemplate() {
  return (
    <div className="grid min-h-dvh place-items-center bg-canvas">
      <Card className="max-w-[380px] text-center" title="Unknown template">
        <p className="text-sm text-ink-2">This M0 build ships a single demo flow.</p>
        <Button to="/" variant="primary" className="mt-3">Back to Home</Button>
      </Card>
    </div>
  );
}
