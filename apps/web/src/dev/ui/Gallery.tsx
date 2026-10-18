import { useState } from "react";
import {
  AccordionSection,
  Banner,
  Button,
  Card,
  ChatBubble,
  Counter,
  DiffCard,
  Dialog,
  DraftQuote,
  Field,
  FilterChip,
  FloatingToolbar,
  Icon,
  IconButton,
  Input,
  LayerRow,
  OverlayBox,
  Progress,
  QuickReplies,
  Select,
  StatusBar,
  StatusPill,
  Switch,
  Tag,
  TemplateCard,
  Textarea,
  Tooltip,
  WorkspaceTopBar,
  useToast,
} from "@templix/ui";

/** Dev-only component gallery — /dev/ui. Visual review + e2e screenshot coverage of every system component. */
export function DevUiGallery() {
  const toast = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [chip, setChip] = useState(true);
  const [zoom, setZoom] = useState(85);

  return (
    <div className="min-h-dvh flex flex-col bg-canvas">
      <WorkspaceTopBar
        back={<span aria-hidden className="grid size-9 place-items-center"><Icon name="layers" className="text-brand" /></span>}
        file="Component Gallery"
        fileMeta="/dev/ui"
        actions={<Button variant="ghost" size="sm" onClick={() => toast({ text: "Toast works", tone: "info" })}>Fire toast</Button>}
      />
      <main className="mx-auto w-full max-w-[1128px] flex-1 space-y-5 px-6 py-6" data-qa="main-content">
        <Section title="Buttons">
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="danger">Danger</Button>
            <Button variant="danger-solid">Danger solid</Button>
            <Button variant="warning-solid">Warning solid</Button>
            <Button size="sm">Small</Button>
            <Button size="lg">Large</Button>
            <Button size="xl">XL</Button>
            <Button loading>Loading</Button>
            <Button disabled>Disabled</Button>
            <Button to="/dev/ui" variant="secondary">Link button</Button>
          </div>
        </Section>

        <Section title="Icon buttons / tooltips">
          <div className="flex flex-wrap items-center gap-3">
            <IconButton icon="save" label="Save" />
            <IconButton icon="undo" label="Undo" />
            <IconButton icon="redo" label="Redo" />
            <IconButton icon="download" label="Export" active />
            <Tooltip content="Tooltip content">
              <Tag tone="neutral">Hover me</Tag>
            </Tooltip>
            <Tooltip content="Top side" side="top">
              <IconButton icon="info" label="Info" tooltipSide="top" />
            </Tooltip>
          </div>
        </Section>

        <Section title="Tags / chips / status pills">
          <div className="flex flex-wrap items-center gap-3">
            <Tag tone="success">Ready</Tag>
            <Tag tone="info">Info</Tag>
            <Tag tone="warning">Needs review</Tag>
            <Tag tone="error">Failed</Tag>
            <Tag tone="neutral">Draft</Tag>
            <Tag tone="brand">Brand</Tag>
            <FilterChip active onClick={() => setChip(!chip)}>Active chip</FilterChip>
            <FilterChip onClick={() => setChip(!chip)}>Chip</FilterChip>
            <StatusPill tone="success" icon="check_circle">Configured</StatusPill>
            <StatusPill tone="warning" icon="warning">Warning</StatusPill>
            <StatusPill tone="error" icon="close">Error</StatusPill>
          </div>
        </Section>

        <Section title="Cards">
          <div className="grid gap-4 min-[700px]:grid-cols-2">
            <Card
              title="Plain card"
              action={<Button variant="ghost" size="sm">Action</Button>}
              footer={<span className="text-xs text-ink-2">Footer</span>}
            >
              <p className="text-sm text-ink-2">Card body text.</p>
            </Card>
            <Card title="File chip">
              <span className="inline-flex h-9 max-w-80 items-center gap-2 rounded-pill bg-canvas px-3 text-sm">
                <Icon name="description" className="text-ink-2" />
                reference.pdf
              </span>
            </Card>
          </div>
          <div className="mt-4 grid gap-4 min-[700px]:grid-cols-3">
            <TemplateCard name="Newsletter template" meta="12 layers · 2 pages"  status="ready" />
            <TemplateCard name="Needs review" meta="8 layers · 1 page"  status="needs-review" />
            <TemplateCard name="Processing" meta="18 layers · 6 pages"  status="processing" progressPercent={62} />
          </div>
        </Section>

        <Section title="Form fields">
          <div className="grid gap-4 min-[700px]:grid-cols-3">
            <Field label="Headline" htmlFor="g-head" counter={<Counter value={42} max={65} />}>
              <Input id="g-head" defaultValue="A perfectly sized headline" />
            </Field>
            <Field label="Over limit" htmlFor="g-over" counter={<Counter value={70} max={65} />} error="Over by 5 characters">
              <Input id="g-over" invalid defaultValue="This headline is definitely too long for the frame" />
            </Field>
            <Field label="Body" htmlFor="g-body" counter={<Counter value={196} max={200} count="words" />}>
              <Textarea id="g-body" rows={3} defaultValue="Long-form body copy for the slot…" />
            </Field>
          </div>
          <div className="mt-4 grid gap-4 min-[700px]:grid-cols-3">
            <Field label="Section" htmlFor="g-select">
              <Select id="g-select" defaultValue="cover">
                <option value="cover">Cover & Masthead</option>
                <option value="lead">Lead Story</option>
              </Select>
            </Field>
            <div className="flex items-end gap-6 pb-2">
              <label className="flex items-center gap-2 text-sm">
                <Switch checked onCheckedChange={() => {}} label="Editable switch" />
                Editable
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Switch checked={false} onCheckedChange={() => {}} label="Locked switch" />
                Locked
              </label>
            </div>
          </div>
        </Section>

        <Section title="Banners / progress">
          <div className="space-y-3">
            <Banner tone="info" title="Info banner">Body copy for the info.</Banner>
            <Banner tone="success" title="Success">Saved.</Banner>
            <Banner tone="warning" title="Warning">Contrast below target.</Banner>
            <Banner tone="error" title="Error">Export failed.</Banner>
            <Progress value={45} label="Step 3 / 7" />
          </div>
        </Section>

        <Section title="Accordion / dialog">
          <div className="grid gap-4 min-[700px]:grid-cols-2">
            <div className="rounded-card bg-card">
              <AccordionSection title="Cover & Masthead" state={{ label: "Complete", tone: "success" }} open onToggle={() => {}}>
                <p className="text-sm text-ink-2">Section body.</p>
              </AccordionSection>
              <AccordionSection title="Lead Story" state={{ label: "Active sync", tone: "info" }} open={false} onToggle={() => {}}>
                <p className="text-sm text-ink-2">Hidden body.</p>
              </AccordionSection>
            </div>
            <div>
              <Button variant="secondary" onClick={() => setDialogOpen(true)}>Open dialog</Button>
              <Dialog open={dialogOpen} onOpenChange={setDialogOpen} title="Dialog title" description="Dialog description.">
                <p className="text-sm">Dialog content.</p>
              </Dialog>
            </div>
          </div>
        </Section>

        <Section title="Editor widgets">
          <div className="grid gap-4 min-[700px]:grid-cols-2">
            <div className="relative h-64 overflow-hidden rounded-card bg-canvas">
              <OverlayBox x={20} y={24} w={120} h={40} roleClass="headings" label="Title" />
              <OverlayBox x={20} y={72} w={180} h={56} roleClass="text" label="Body" selected />
              <OverlayBox x={220} y={24} w={90} h={60} roleClass="media" label="Image" />
              <OverlayBox x={220} y={92} w={90} h={40} roleClass="review" label="Callout" review="Low contrast" />
            </div>
            <div className="space-y-3">
              <FloatingToolbar
                zoom={{
                  value: zoom,
                  set: (v) => setZoom(Math.min(400, Math.max(25, v))),
                  step: (dir) => setZoom((v) => Math.min(400, Math.max(25, v + dir * 10))),
                  fit: () => setZoom(85),
                }}
                page={{ label: "1 / 2" }}
                toggles={[{ key: "grid", label: "Show grid", icon: "grid_4x4", checked: false, onChange: () => {} }]}
              />
              <LayerRow name="Title: Campus Chronicle" roleLabel="Heading 1" state={{ kind: "editable-outlined" }} editable onToggleEditable={() => {}} />
              <LayerRow name="Callout Quote" roleLabel="Quote" state={{ kind: "review", reason: "Low Contrast" }} />
              <LayerRow name="Story Photo" roleLabel="Image" state={{ kind: "slot", slotLabel: "Story Photo" }} />
              <LayerRow name="Divider Line" roleLabel="Shape" state={{ kind: "fixed" }} locked />
            </div>
          </div>
        </Section>

        <Section title="AI surfaces / chat">
          <div className="grid gap-4 min-[700px]:grid-cols-2">
            <DiffCard
              slotLabel="Story Headline"
              slotMeta="Page 1 · Lead Story"
              counter="58 / 65 max chars"
              counterTone="safe"
              original="Original headline from the PDF"
              proposal="Proposed headline from the assistant"
              targetNote="Target: 2 lines exact"
            />
            <div className="space-y-3">
              <ChatBubble side="assistant" author="Templix Assist">
                Here is a draft:
                <DraftQuote>Proposed headline draft copy</DraftQuote>
              </ChatBubble>
              <ChatBubble side="user">Looks good, ship it.</ChatBubble>
              <QuickReplies replies={["Accept all", "Skip slot", "Try another"]} />
            </div>
          </div>
        </Section>

        <Section title="Status bar">
          <div className="-m-4 rounded-b-card bg-card">
            <StatusBar left={{ engine: "Engine ready", ram: "284 MB", parser: "PDF v0" }} privacyMode="No telemetry" version="0.1.0" />
          </div>
        </Section>
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <Card title={title}>{children}</Card>;
}
