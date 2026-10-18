import { useState } from "react";
import { Link, useParams } from "react-router";
import {
  AccordionSection,
  Banner,
  Button,
  Card,
  Counter,
  Field,
  FloatingToolbar,
  Icon,
  Input,
  StatusBar,
  Tag,
  Textarea,
  WorkspaceTopBar,
  counterState,
} from "@templix/ui";
import { APP_VERSION } from "../lib/version";
import { copy } from "../lib/copy";
import { fixtureManualDoc, PAGE_H, PAGE_SCALE, PAGE_W, type DemoSlot } from "../fixtures/demo";

export function ManualEditorScreen() {
  const { documentId } = useParams();
  const d = fixtureManualDoc;
  const [zoom, setZoom] = useState(Math.round(PAGE_SCALE * 100));
  const [activeSection, setActiveSection] = useState(d.sections[0]?.id ?? "");
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(d.sections.flatMap((s) => s.slots.map((sl) => [sl.id, sl.value]))),
  );
  const [open, setOpen] = useState<Record<string, boolean>>(Object.fromEntries(d.sections.map((s) => [s.id, true])));

  if (documentId !== d.documentId) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="max-w-[380px] text-center" title="Unknown document">
          <Button to="/" variant="primary" className="mt-3">Back to Home</Button>
        </Card>
      </div>
    );
  }

  const z = zoom / 100;
  const headlineLen = (values["sl_headline"] ?? "").length;

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={<Link to={`/templates/t_newsletter/mode`} aria-label="Back to mode picker" className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4"><Icon name="arrow_back" /></Link>}
        file={d.title}
        fileMeta={`Page ${d.pageNum} / ${d.pageCount}`}
        status={<Tag tone="success" icon={<Icon name="check_circle" className="text-[14px]" />}>{d.autosaved ? "Saved just now" : "Saving…"}</Tag>}
        actions={
          <>
            <span title={copy.fidelity.tooltip} className="hidden items-center gap-1 rounded-pill bg-success-bg px-2.5 py-1 text-label-sm text-success min-[1100px]:inline-flex">
              <Icon name="verified_user" className="text-[14px]" />
              Fidelity {(d.fidelity * 100).toFixed(1)}%
            </span>
            <Button variant="secondary" size="sm" leading={<Icon name="picture_as_pdf" className="text-[16px]" />}>Export PDF</Button>
          </>
        }
      />

      <div className="flex min-h-0 flex-1">
        {/* Left: sections */}
        <aside className="flex w-[280px] shrink-0 flex-col border-r border-border bg-card" data-qa="sidebar-left">
          <div className="flex h-12 items-center border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">Sections</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {d.sections.map((s) => (
              <AccordionSection
                key={s.id}
                title={s.label}
                state={{ label: s.status.label, tone: s.status.tone }}
                open={open[s.id] ?? false}
                onToggle={() => setOpen((o) => ({ ...o, [s.id]: !o[s.id] }))}
              >
                {s.slots.length === 0 ? (
                  <p className="text-xs text-ink-2">{s.repeater?.instances.length ?? 0} repeater instances · {s.repeater?.max ?? 0} max</p>
                ) : (
                  <ul className="space-y-1">
                    {s.slots.map((sl) => (
                      <li key={sl.id}>
                        <button
                          type="button"
                          onClick={() => setActiveSection(s.id)}
                          className={`w-full truncate rounded px-2 py-1 text-left text-xs ${activeSection === s.id ? "bg-brand-tint text-brand" : "text-ink-2 hover:bg-black/4"}`}
                        >
                          {sl.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </AccordionSection>
            ))}
          </div>
        </aside>

        {/* Center: canvas */}
        <div className="relative min-w-0 flex-1 overflow-auto bg-canvas" data-qa="canvas-viewport">
          <div className="flex min-h-full items-start justify-center p-6 pb-24">
            <div className="relative" style={{ width: PAGE_W * z, height: PAGE_H * z }}>
              <div
                data-qa="canvas"
                className="relative overflow-hidden rounded-sm border border-border/80 bg-card shadow-l2"
                style={{ width: PAGE_W * z, height: PAGE_H * z }}
              >
                {/* sync-outline around active headline slot (live feedback) */}
                <div
                  className="absolute border-2 border-brand transition-all"
                  style={{ left: 48 * z, top: 188 * z, width: 380 * z, height: 64 * z, opacity: activeSection === "s_lead" ? 1 : 0.25 }}
                />
                <p className="absolute font-extrabold tracking-tight text-ink" style={{ left: 48 * z, top: 72 * z, fontSize: 36 * z }}>CAMPUS CHRONICLE</p>
                <p className="absolute text-label-sm uppercase tracking-wider text-brand" style={{ left: 48 * z, top: 130 * z, fontSize: 11 * z }}>March 2025 · Issue 4</p>
                <p className="absolute font-semibold leading-tight text-ink" style={{ left: 48 * z, top: 196 * z, width: 380 * z, fontSize: 20 * z }}>
                  {values["sl_headline"] ?? ""}
                </p>
                <div className="absolute grid place-items-center gap-1 bg-brand-tint/60" style={{ left: 48 * z, top: 264 * z, width: 246 * z, height: 150 * z }}>
                  <Icon name="image" className="text-brand" />
                  <span className="px-2 text-center text-[10px] font-medium text-brand">lab_opening_day.jpg · 300×200 crop</span>
                </div>
                <p className="absolute text-ink-2" style={{ left: 48 * z, top: 428 * z, width: 246 * z, fontSize: 12 * z, lineHeight: 1.45 }}>
                  {values["sl_body"] ?? ""}
                </p>
                <p className="absolute text-center text-[10px] text-ink-2" style={{ left: 48 * z, top: 734 * z, width: 516 * z }}>
                  Campus Chronicle • Student Affairs Publication Office
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
                page={{ label: `${d.pageNum} / ${d.pageCount}` }}
                toggles={[
                  { key: "layers", label: "Show sync outline", icon: "layers", checked: true, onChange: () => {} },
                ]}
              />
            </div>
          </div>
        </div>

        {/* Right: slot editor */}
        <aside className="flex w-[340px] shrink-0 flex-col border-l border-border bg-card" data-qa="sidebar-right">
          <div className="flex h-12 items-center border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">Slot editor</span>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {headlineLen > 0 && (
              <Banner tone={counterState(headlineLen, 65) === "ok" ? "success" : "warning"} title="Headline frame check">
                <span className="text-sm">
                  {counterState(headlineLen, 65) === "ok"
                    ? `Headline fits the locked frame at ${Math.round(PAGE_SCALE * 100)}% scale.`
                    : "Headline wraps beyond the locked 2-line frame — shorten or reduce size in the template."}
                </span>
              </Banner>
            )}
            <SlotField slot={d.sections.flatMap((s) => s.slots).find((s) => s.id === "sl_title")!} value={values["sl_title"] ?? ""} onChange={(v) => setValues((s) => ({ ...s, sl_title: v }))} />
            <SlotField slot={d.sections.flatMap((s) => s.slots).find((s) => s.id === "sl_headline")!} value={values["sl_headline"] ?? ""} onChange={(v) => setValues((s) => ({ ...s, sl_headline: v }))} />
            <SlotField slot={d.sections.flatMap((s) => s.slots).find((s) => s.id === "sl_byline")!} value={values["sl_byline"] ?? ""} onChange={(v) => setValues((s) => ({ ...s, sl_byline: v }))} />

            {/* image slot */}
            <Card className="p-3" title={<span className="text-label-md">Feature Image</span>}>
              <div className="flex items-center gap-3">
                <span className="grid size-16 place-items-center rounded border border-border bg-canvas"><Icon name="image" className="text-ink-2" /></span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-ink">lab_opening_day.jpg</p>
                  <p className="text-xs text-ink-2">300×200 crop · size not shown (fixture)</p>
                  <div className="mt-1 flex gap-2">
                    <Button variant="ghost" size="sm" leading={<Icon name="swap_horiz" className="text-[14px]" />}>Replace</Button>
                    <Button variant="ghost" size="sm" leading={<Icon name="crop_free" className="text-[14px]" />}>Adjust crop</Button>
                  </div>
                </div>
              </div>
            </Card>

            {/* repeater */}
            <Card className="p-3" title={<span className="text-label-md">Articles & Highlights</span>} action={<Tag tone="neutral">{d.sections[2]?.repeater?.instances.length ?? 0}/{d.sections[2]?.repeater?.max ?? 0}</Tag>}>
              <ul className="space-y-1">
                {d.sections[2]?.repeater?.instances.map((inst, i) => (
                  <li key={inst.id} className="flex items-center gap-2 rounded border border-border px-2 py-1.5">
                    <span className="text-xs tabular-nums text-ink-2">#{i + 1}</span>
                    <span className="min-w-0 flex-1 truncate text-sm text-ink">{inst.title}</span>
                    <span className="text-xs tabular-nums text-ink-2">{inst.words}w</span>
                    <button type="button" aria-label={`Move up article ${i + 1}`} className="text-ink-2 hover:text-ink"><Icon name="expand_less" className="text-[16px]" /></button>
                    <button type="button" aria-label={`Remove article ${i + 1}`} className="text-ink-2 hover:text-error"><Icon name="close" className="text-[16px]" /></button>
                  </li>
                ))}
              </ul>
            </Card>

            {/* rules summary */}
            <Card className="p-3" title={<span className="text-label-md">Rules passed</span>} action={<Tag tone="success">{d.rulesPassed.passed} rules</Tag>}>
              <p className="text-xs text-ink-2">{d.rulesPassed.kinds.join(" · ")}</p>
            </Card>
          </div>
          <div className="border-t border-border p-3">
            <Button
              to={`/documents/${d.documentId}/ai`}
              variant="secondary"
              className="w-full"
              leading={<Icon name="auto_awesome" className="text-[16px]" />}
            >
              Switch to AI Assist
            </Button>
          </div>
        </aside>
      </div>

      <StatusBar
        left={{ engine: "Engine ready", detail: `Fidelity ${(d.fidelity * 100).toFixed(1)}%`, ram: "—", parser: "Autosave: on" }}
        privacyMode="Manual Edit: local only"
        version={APP_VERSION}
      />
    </div>
  );
}

function SlotField({ slot, value, onChange }: { slot: DemoSlot; value: string; onChange: (v: string) => void }) {
  const max = slot.maxChars ?? slot.maxWords ?? 0;
  const over = max > 0 && value.length > max;
  return (
    <Field
      label={slot.label}
      htmlFor={slot.id}
      counter={max > 0 ? <Counter value={value.length} max={max} count={slot.maxWords ? "words" : "chars"} /> : undefined}
      error={over ? `Over the ${slot.maxWords ? "word" : "character"} limit by ${value.length - max}` : undefined}
    >
      {slot.kind === "richtext" ? (
        <Textarea id={slot.id} invalid={over} value={value} onChange={(e) => onChange(e.target.value)} rows={5} />
      ) : (
        <Input id={slot.id} invalid={over} value={value} onChange={(e) => onChange(e.target.value)} />
      )}
    </Field>
  );
}
