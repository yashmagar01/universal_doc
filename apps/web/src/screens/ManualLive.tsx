import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import {
  Banner,
  Button,
  Card,
  Counter,
  Field,
  FloatingToolbar,
  Icon,
  OverlayBox,
  StatusBar,
  Tag,
  Textarea,
  WorkspaceTopBar,
} from "@templix/ui";
import type { Node, Run, Slot, Template } from "@templix/doc-schema";
import {
  downloadExport,
  ensureSession,
  getDocument,
  getTemplate,
  referenceUrl,
  setSlot,
  type DocumentResponse,
} from "../lib/api";
import { APP_VERSION } from "../lib/version";
import { useLiveStatus } from "../lib/useStatus";

type SaveState = "saved" | "saving" | "error";

const HEADING_ROLES = new Set(["title", "heading1", "heading2"]);
const AUTOSAVE_MS = 600;

function fitZoom(width: number, height: number): number {
  return Math.round(Math.min(1.2, 820 / width, 820 / height) * 100);
}

function flatten(nodes: Node[]): Node[] {
  return nodes.flatMap((node) => (node.type === "group" ? flatten(node.children ?? []) : [node]));
}

function runsText(runs: Run[] | null | undefined): string {
  return (runs ?? []).map((run) => run.text).join("");
}

function originalText(template: Template, slot: Slot): string {
  for (const page of template.pages ?? []) {
    for (const node of flatten(page.nodes ?? [])) {
      if (slot.nodeIds.includes(node.id)) return runsText(node.runs);
    }
  }
  return "";
}

function slotPage(template: Template, slot: Slot): number {
  for (const [index, page] of (template.pages ?? []).entries()) {
    if (flatten(page.nodes ?? []).some((node) => slot.nodeIds.includes(node.id))) return index + 1;
  }
  return 1;
}

/** Live manual editor: original PDF as the visual reference, real slots persisted through the op log. */
export function ManualLive() {
  const { documentId } = useParams();
  const live = useLiveStatus();
  const [doc, setDoc] = useState<DocumentResponse | null>(null);
  const [template, setTemplate] = useState<Template | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [pageIndex, setPageIndex] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [activeSlot, setActiveSlot] = useState<string | null>(null);

  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const dirty = useRef<Map<string, string>>(new Map());
  const chain = useRef<Promise<void>>(Promise.resolve());
  const pending = useRef(0);
  const failed = useRef(false);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    const timerMap = timers.current;
    return () => {
      alive.current = false;
      for (const timer of timerMap.values()) clearTimeout(timer);
      timerMap.clear();
    };
  }, []);

  useEffect(() => {
    if (!documentId) return;
    let liveRequest = true;
    ensureSession()
      .then(() => getDocument(documentId))
      .then(async (body) => {
        const nextTemplate = await getTemplate(body.templateId);
        if (!liveRequest) return;
        setDoc(body);
        setTemplate(nextTemplate);
        setValues(
          Object.fromEntries(
            (nextTemplate.slots ?? []).map((slot) => {
              const stored = body.content?.values?.[slot.id];
              return [slot.id, stored === undefined ? originalText(nextTemplate, slot) : runsText(stored)];
            }),
          ),
        );
        const first = nextTemplate.pages?.[0];
        if (first) setZoom(fitZoom(first.size.w, first.size.h));
        setSaveState("saved");
      })
      .catch((err: unknown) => {
        if (liveRequest) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      liveRequest = false;
    };
  }, [documentId]);

  const nodeIndex = useMemo(() => {
    const index = new Map<string, Node>();
    for (const page of template?.pages ?? []) {
      for (const node of flatten(page.nodes ?? [])) index.set(node.id, node);
    }
    return index;
  }, [template]);

  const nodeToSlot = useMemo(() => {
    const map = new Map<string, Slot>();
    for (const slot of template?.slots ?? []) {
      for (const nodeId of slot.nodeIds) map.set(nodeId, slot);
    }
    return map;
  }, [template]);

  const slots = useMemo(() => {
    return [...(template?.slots ?? [])].sort((a, b) => {
      const an = nodeIndex.get(a.nodeIds[0] ?? "");
      const bn = nodeIndex.get(b.nodeIds[0] ?? "");
      return (
        (an?.provenance?.page ?? 0) - (bn?.provenance?.page ?? 0) ||
        (an?.bbox.y ?? 0) - (bn?.bbox.y ?? 0)
      );
    });
  }, [template, nodeIndex]);

  const textSlots = useMemo(() => slots.filter((slot) => slot.kind !== "image"), [slots]);
  const imageSlots = useMemo(() => slots.filter((slot) => slot.kind === "image"), [slots]);
  const pages = template?.pages ?? [];
  const page = pages[Math.min(pageIndex, Math.max(pages.length - 1, 0))];
  const pageW = page?.size.w ?? 612;
  const pageH = page?.size.h ?? 792;
  const z = zoom / 100;
  const nodesOnPage = useMemo(() => {
    return flatten(page?.nodes ?? []).flatMap((node) => {
      const slot = nodeToSlot.get(node.id);
      return slot ? [{ node, slot }] : [];
    });
  }, [page, nodeToSlot]);

  function enqueue(slotId: string): void {
    const text = dirty.current.get(slotId);
    if (text === undefined || !documentId) return;
    dirty.current.delete(slotId);
    pending.current += 1;
    setSaveState("saving");
    chain.current = chain.current.then(async () => {
      try {
        await setSlot(documentId, slotId, text);
        pending.current -= 1;
        failed.current = false;
        if (
          alive.current &&
          pending.current === 0 &&
          dirty.current.size === 0 &&
          timers.current.size === 0
        ) {
          setSaveState("saved");
          setSaveError(null);
        }
      } catch (err: unknown) {
        pending.current -= 1;
        failed.current = true;
        if (!dirty.current.has(slotId)) dirty.current.set(slotId, text);
        if (alive.current) {
          setSaveState("error");
          setSaveError(err instanceof Error ? err.message : String(err));
        }
      }
    });
  }

  function scheduleSave(slotId: string, text: string): void {
    dirty.current.set(slotId, text);
    setSaveState("saving");
    const existing = timers.current.get(slotId);
    if (existing) clearTimeout(existing);
    timers.current.set(
      slotId,
      setTimeout(() => {
        timers.current.delete(slotId);
        enqueue(slotId);
      }, AUTOSAVE_MS),
    );
  }

  function flushSlot(slotId: string): void {
    const timer = timers.current.get(slotId);
    if (timer) clearTimeout(timer);
    timers.current.delete(slotId);
    enqueue(slotId);
  }

  async function flushAll(): Promise<void> {
    for (const [slotId, timer] of timers.current) {
      clearTimeout(timer);
      timers.current.delete(slotId);
      enqueue(slotId);
    }
    for (const slotId of [...dirty.current.keys()]) enqueue(slotId);
    await chain.current;
  }

  async function onRetry(): Promise<void> {
    failed.current = false;
    setSaveError(null);
    await flushAll();
    if (!failed.current) setSaveState("saved");
  }

  async function onExport(): Promise<void> {
    if (!documentId || !template) return;
    setExporting(true);
    setExportError(null);
    try {
      await flushAll();
      if (failed.current) throw new Error("Some edits are not saved. Retry the save first.");
      const blob = await downloadExport(documentId);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = `${template.name || "document"}.pdf`;
      link.rel = "noopener";
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err: unknown) {
      setExportError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(false);
    }
  }

  function focusSlot(slotId: string): void {
    setActiveSlot(slotId);
    window.document
      .getElementById(`slot-${slotId}`)
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  if (error) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="max-w-[420px] text-center" title="Document not available">
          <p className="text-sm text-ink-2" role="alert">
            {error}
          </p>
          <div className="mt-3 flex justify-center gap-2">
            <Button to="/documents" variant="primary">
              All documents
            </Button>
            <Button to="/" variant="ghost">
              Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!doc || !template) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="w-[360px]" title="Opening draft">
          <p className="text-sm text-ink-2">Loading document and template…</p>
        </Card>
      </div>
    );
  }

  const saveTag =
    saveState === "error" ? (
      <Tag tone="error" icon={<Icon name="warning" className="text-[14px]" />}>
        Save failed
      </Tag>
    ) : saveState === "saving" ? (
      <Tag tone="info" icon={<Icon name="refresh" className="text-[14px]" />}>
        Saving…
      </Tag>
    ) : (
      <Tag tone="success" icon={<Icon name="check_circle" className="text-[14px]" />}>
        Saved
      </Tag>
    );

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={
          <Link
            to={`/templates/${template.id}/analysis`}
            aria-label="Back to analysis"
            className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4"
          >
            <Icon name="arrow_back" />
          </Link>
        }
        file={template.name}
        fileMeta={`${pages.length} pages · ${slots.length} slots`}
        userName="Local user"
        userRole="This device"
        status={<span data-qa="save-status" data-state={saveState}>{saveTag}</span>}
        actions={
          <>
            <Button to="/documents" variant="ghost" size="sm">
              Documents
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={exporting}
              onClick={() => void onExport()}
              leading={<Icon name="picture_as_pdf" className="text-[16px]" />}
            >
              Export PDF
            </Button>
          </>
        }
      />

      <div className="flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1 overflow-auto bg-canvas" data-qa="editor-canvas-viewport">
          <div className="flex min-h-full items-start justify-center p-6 pb-24">
            <div className="relative" style={{ width: pageW * z, height: pageH * z }}>
              <div
                data-qa="editor-canvas"
                className="relative overflow-hidden rounded-sm border border-border/80 bg-white shadow-l2"
                style={{ width: pageW * z, height: pageH * z }}
              >
                {page?.referenceSha ? (
                  <img
                    data-qa="page-reference"
                    src={referenceUrl(template.id, pageIndex)}
                    alt={`Page ${pageIndex + 1} reference`}
                    className="absolute inset-0 h-full w-full object-contain"
                  />
                ) : (
                  <div className="absolute inset-0 bg-white" />
                )}
                {nodesOnPage.map(({ node, slot }) => (
                  <OverlayBox
                    key={node.id}
                    x={node.bbox.x * z}
                    y={node.bbox.y * z}
                    w={node.bbox.w * z}
                    h={node.bbox.h * z}
                    roleClass={
                      slot.kind === "image"
                        ? "media"
                        : HEADING_ROLES.has(node.role)
                          ? "headings"
                          : "text"
                    }
                    label={slot.label}
                    selected={activeSlot === slot.id}
                    handleCount={0}
                    handleClick={() => focusSlot(slot.id)}
                    className="z-10"
                  />
                ))}
              </div>
              <FloatingToolbar
                className="absolute top-4 left-1/2 z-20 -translate-x-1/2"
                zoom={{
                  value: zoom,
                  set: (v) => setZoom(Math.min(400, Math.max(25, v))),
                  step: (dir) => setZoom((v) => Math.min(400, Math.max(25, v + dir * 10))),
                  fit: () => setZoom(fitZoom(pageW, pageH)),
                }}
                page={{
                  label: `${pageIndex + 1} / ${Math.max(pages.length, 1)}`,
                  prev:
                    pageIndex > 0
                      ? () => {
                          setPageIndex((index) => index - 1);
                          setActiveSlot(null);
                        }
                      : undefined,
                  next:
                    pageIndex < pages.length - 1
                      ? () => {
                          setPageIndex((index) => index + 1);
                          setActiveSlot(null);
                        }
                      : undefined,
                }}
              />
            </div>
          </div>
        </div>

        <aside className="flex w-[360px] shrink-0 flex-col border-l border-border bg-card" data-qa="sidebar-right">
          <div className="flex h-12 items-center justify-between border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">
              Content
            </span>
            <span className="text-xs text-ink-2">
              {textSlots.length} editable {textSlots.length === 1 ? "field" : "fields"}
            </span>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {saveError && (
              <Banner
                tone="error"
                title="Save failed"
                actions={
                  <Button size="sm" variant="secondary" onClick={() => void onRetry()}>
                    Retry
                  </Button>
                }
              >
                <span className="text-sm">{saveError}</span>
              </Banner>
            )}
            {exportError && (
              <Banner tone="error" title="Export failed">
                <span className="text-sm">{exportError}</span>
              </Banner>
            )}
            {textSlots.length === 0 && (
              <p className="text-sm text-ink-2">
                This template has no editable text slots. The original PDF is still exportable.
              </p>
            )}
            {textSlots.map((slot) => (
              <div key={slot.id} id={`slot-${slot.id}`} data-qa="slot-field">
                <Field
                  label={
                    <span>
                      {slot.label}
                      <span className="ml-2 text-xs font-normal text-ink-2">
                        Page {slotPage(template, slot)}
                      </span>
                    </span>
                  }
                  htmlFor={`input-${slot.id}`}
                  required={slot.required}
                  counter={
                    slot.constraints?.maxChars && slot.constraints.maxChars > 0 ? (
                      <Counter value={values[slot.id]?.length ?? 0} max={slot.constraints.maxChars} />
                    ) : undefined
                  }
                  error={
                    slot.constraints?.maxChars &&
                    (values[slot.id]?.length ?? 0) > slot.constraints.maxChars
                      ? `Over the character limit by ${(values[slot.id]?.length ?? 0) - slot.constraints.maxChars}`
                      : undefined
                  }
                >
                  <Textarea
                    id={`input-${slot.id}`}
                    data-qa="slot-input"
                    rows={Math.min(8, Math.max(2, slot.constraints?.maxLines ?? 2))}
                    invalid={
                      Boolean(slot.constraints?.maxChars) &&
                      (values[slot.id]?.length ?? 0) > (slot.constraints?.maxChars ?? 0)
                    }
                    value={values[slot.id] ?? ""}
                    onFocus={() => setActiveSlot(slot.id)}
                    onChange={(event) => {
                      const text = event.target.value;
                      setValues((current) => ({ ...current, [slot.id]: text }));
                      scheduleSave(slot.id, text);
                    }}
                    onBlur={() => flushSlot(slot.id)}
                  />
                </Field>
              </div>
            ))}
            {imageSlots.length > 0 && (
              <Card className="p-3" title={<span className="text-label-md">Images</span>}>
                <p className="text-xs text-ink-2">
                  {imageSlots.length} image {imageSlots.length === 1 ? "slot is" : "slots are"} preserved
                  from the original PDF. Image replacement is not part of this build.
                </p>
              </Card>
            )}
          </div>
          <div className="border-t border-border p-3">
            <p className="text-xs text-ink-2">
              Export keeps the original layout and replaces only the text you changed.
            </p>
          </div>
        </aside>
      </div>

      <StatusBar
        left={{
          engine: "Engine ready",
          detail: `Draft · ${slots.length} slots`,
          ram: live?.ram ?? "—",
          parser: live?.parser ?? "Export: local",
        }}
        privacyMode="Manual edit: local only"
        version={APP_VERSION}
      />
    </div>
  );
}
