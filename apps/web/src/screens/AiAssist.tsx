import { useState } from "react";
import { Link, useParams } from "react-router";
import {
  Banner,
  Button,
  Card,
  ChatBubble,
  DiffCard,
  DraftQuote,
  FloatingToolbar,
  Icon,
  IconButton,
  Input,
  Progress,
  QuickReplies,
  StatusBar,
  Tag,
  WorkspaceTopBar,
} from "@templix/ui";
import { APP_VERSION } from "../lib/version";
import { copy } from "../lib/copy";
import { fixtureAi, PAGE_H, PAGE_SCALE, PAGE_W } from "../fixtures/demo";

const STEPS = [
  "Cover & Masthead",
  "Issue Line",
  "Lead Story Headline",
  "Byline",
  "Lead Story Body",
  "Callout Quote",
  "Footer",
];

export function AiAssistScreen() {
  const { documentId } = useParams();
  const a = fixtureAi;
  const [zoom, setZoom] = useState(Math.round(PAGE_SCALE * 100));
  const [composer, setComposer] = useState("");

  if (documentId !== a.documentId) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="max-w-[380px] text-center" title="Unknown document">
          <Button to="/" variant="primary" className="mt-3">Back to Home</Button>
        </Card>
      </div>
    );
  }

  const z = zoom / 100;

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={<Link to="/documents/d_march/manual" aria-label="Back to manual editor" className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4"><Icon name="arrow_back" /></Link>}
        file={`Campus Chronicle - March Draft`}
        fileMeta={`AI Assist · Step ${a.step} of ${a.stepTotal}`}
        status={
          <Tag tone="brand" icon={<Icon name="smart_toy" className="text-[14px]" />}>
            {a.providerLabel} · {a.modelId}
          </Tag>
        }
        actions={
          <>
            <span className="hidden text-xs text-ink-2 min-[1100px]:inline">Latency {a.latencyMs} ms · provider {a.providerLabel}</span>
            <Button variant="secondary" size="sm" leading={<Icon name="picture_as_pdf" className="text-[16px]" />}>Export PDF</Button>
          </>
        }
      />

      <div className="flex min-h-0 flex-1">
        {/* Left: step list */}
        <aside className="flex w-[280px] shrink-0 flex-col border-r border-border bg-card" data-qa="sidebar-left">
          <div className="flex h-12 items-center border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">Draft steps</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <ul className="space-y-1">
              {STEPS.map((s, i) => {
                const n = i + 1;
                const state = n < a.step ? "done" : n === a.step ? "current" : "todo";
                return (
                  <li key={s}>
                    <div
                      data-qa="step-row"
                      className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-sm ${state === "current" ? "bg-brand-tint font-medium text-brand" : "text-ink-2"}`}
                    >
                      <Icon
                        name={state === "done" ? "check_circle" : state === "current" ? "auto_awesome" : "chevron_right"}
                        className={`shrink-0 text-[16px] ${state === "done" ? "text-success" : state === "current" ? "text-brand" : "text-ink-2"}`}
                      />
                      <span className="min-w-0 flex-1 truncate">{s}</span>
                      {state === "done" && <Tag tone="success">Done</Tag>}
                      {state === "current" && <Tag tone="brand">Now</Tag>}
                    </div>
                  </li>
                );
              })}
            </ul>
            <div className="mt-4">
              <p className="mb-1 text-label-sm text-ink-2">
                Step {a.step} / {a.stepTotal} · {a.stepLabel}
              </p>
              <Progress value={a.stepPct} />
            </div>
          </div>
        </aside>

        {/* Center: canvas with current slot highlighted */}
        <div className="relative min-w-0 flex-1 overflow-auto bg-canvas" data-qa="canvas-viewport">
          <div className="flex min-h-full items-start justify-center p-6 pb-24">
            <div className="relative" style={{ width: PAGE_W * z, height: PAGE_H * z }}>
              <div
                data-qa="canvas"
                className="relative overflow-hidden rounded-sm border border-border/80 bg-card shadow-l2"
                style={{ width: PAGE_W * z, height: PAGE_H * z }}
              >
                <div
                  className="absolute border-2 border-brand"
                  style={{ left: 48 * z, top: 188 * z, width: 380 * z, height: 64 * z }}
                />
                <p className="absolute font-extrabold tracking-tight text-ink" style={{ left: 48 * z, top: 72 * z, fontSize: 36 * z }}>CAMPUS CHRONICLE</p>
                <p className="absolute font-semibold leading-tight text-ink" style={{ left: 48 * z, top: 196 * z, width: 380 * z, fontSize: 20 * z }}>
                  New Local AI Laboratories Open for Collaborative Research Projects
                </p>
                <div className="absolute grid place-items-center bg-brand-tint/60" style={{ left: 48 * z, top: 264 * z, width: 246 * z, height: 150 * z }}>
                  <Icon name="image" className="text-brand" />
                </div>
                <p className="absolute text-ink-2" style={{ left: 48 * z, top: 428 * z, width: 246 * z, fontSize: 12 * z, lineHeight: 1.45 }}>
                  University administration has officially ratified the digital privacy initiative…
                </p>
              </div>
              <FloatingToolbar
                className="absolute top-4 left-1/2 -translate-x-1/2 z-20"
                zoom={{
                  value: zoom,
                  set: (v) => setZoom(Math.min(400, Math.max(25, v))),
                  step: (dir) => setZoom((v) => Math.min(400, Math.max(25, v + dir * 10))),
                  fit: () => setZoom(Math.round(PAGE_SCALE * 100)),
                }}
                page={{ label: `1 / 2` }}
              />
            </div>
          </div>
        </div>

        {/* Right: chat + proposals */}
        <aside className="flex w-[360px] shrink-0 flex-col border-l border-border bg-card" data-qa="sidebar-right">
          <div className="flex h-12 items-center justify-between border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">Assistant</span>
            <span className="text-xs tabular-nums text-ink-2">
              {a.proposals.pending} pending · {a.proposals.accepted} accepted
            </span>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-3">
            <Banner tone="info" title={copy.ai.protection} className="text-body-sm" >
              <span className="text-sm">{a.proposals.fitsAll ? copy.ai.fitOk : "Some proposals exceed slot limits — flagged below."}</span>
            </Banner>

            {a.messages.map((m) => (
              <ChatBubble key={m.id} side={m.side as "assistant" | "user"} author={m.side === "assistant" ? copy.ai.author : undefined}>
                {m.quote != null ? (
                  <>
                    <span className="block text-sm">{m.text}</span>
                    <DraftQuote label="Current slot">{m.quote}</DraftQuote>
                  </>
                ) : (
                  m.text
                )}
              </ChatBubble>
            ))}

            {a.proposals.cards.map((p) => (
              <DiffCard
                key={p.id}
                slotLabel={p.slot}
                slotMeta={p.meta}
                counter={p.counter}
                counterTone={p.tone === "warn" ? "warn" : "safe"}
                original={p.original}
                proposal={p.proposal}
                targetNote={`Target: ${p.target}`}
                providerNote={`Drafted by ${a.providerLabel} (${a.modelId})`}
              />
            ))}

            <QuickReplies replies={["Accept all", "Skip this slot", "Try another draft", "Go back"]} />
          </div>

          {/* composer: attach / tune / send only — no mic (FR-AI-07, §12-13) */}
          <div className="border-t border-border p-3">
            <div className="flex items-end gap-2">
              <IconButton icon="attach_file" label="Attach reference" />
              <IconButton icon="tune" label="Draft settings" />
              <Input
                value={composer}
                onChange={(e) => setComposer(e.target.value)}
                placeholder="Give instructions for this draft…"
                aria-label="Message to assistant"
                className="flex-1"
              />
              <IconButton icon="send" label="Send instruction" active={composer.length > 0} />
            </div>
          </div>
        </aside>
      </div>

      <StatusBar
        left={{ engine: "Engine ready", detail: `${a.providerLabel} · ${a.modelId}`, ram: "—", parser: "Streaming: idle" }}
        privacyMode={copy.indicator.cloud(a.providerLabel)}
        version={APP_VERSION}
      />
    </div>
  );
}
