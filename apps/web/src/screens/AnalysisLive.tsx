import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import {
  Banner,
  Button,
  Card,
  FloatingToolbar,
  Icon,
  OverlayBox,
  Progress,
  StatusBar,
  Tag,
  WorkspaceTopBar,
  type TagTone,
} from "@templix/ui";
import type { Node, ReviewItem, Template } from "@templix/doc-schema";
import { APP_VERSION } from "../lib/version";
import {
  cancelJob,
  createDocument,
  ensureSession,
  getAnalysis,
  jobEventsUrl,
  referenceUrl,
  type AnalysisResponse,
} from "../lib/api";
import { useLiveStatus } from "../lib/useStatus";

type RoleClass = "headings" | "text" | "media" | "shape" | "review";

const HEADING_ROLES = new Set(["title", "heading1", "heading2"]);
const MEDIA_ROLES = new Set(["image", "figure", "photo", "logo", "background"]);
const SHAPE_ROLES = new Set(["rule", "box", "header", "footer", "pagenum"]);
const OTHER_MEDIA_TYPES = new Set(["image", "shape"]);

/** Leaves under any depth of groups; a group is a container, not a layer. */
function flattenLayers(nodes: Node[]): Node[] {
  return nodes.flatMap((node) =>
    node.type === "group" ? flattenLayers(node.children ?? []) : [node],
  );
}

const ROLE_LABEL: Record<string, string> = {
  title: "Title",
  heading1: "Heading 1",
  heading2: "Heading 2",
  body: "Body text",
  caption: "Caption",
  label: "Label",
  quote: "Quote",
  byline: "Byline",
  header: "Running header",
  footer: "Footer",
  pagenum: "Page number",
  figure: "Image (figure)",
  photo: "Image",
  logo: "Logo",
  background: "Background image",
  rule: "Rule",
  box: "Shape",
  section: "Section",
};

interface JobState {
  jobId?: string;
  fileName?: string;
}

interface ProgressState {
  stage: string;
  message: string;
  progress: number;
}

/** Live analysis screen: SSE progress while ingesting, then the real template + review queue. */
export function AnalysisLive() {
  const { templateId } = useParams();
  const location = useLocation();
  const state = (location.state ?? {}) as JobState;

  const [progress, setProgress] = useState<ProgressState | null>(
    state.jobId ? { stage: "validate", message: "Reading document", progress: 0 } : null,
  );
  const [failure, setFailure] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [cancelRequested, setCancelRequested] = useState(false);
  const jobId = state.jobId;

  useEffect(() => {
    if (!templateId) return;
    let alive = true;
    let source: EventSource | null = null;

    const load = () => {
      ensureSession()
        .then(() => getAnalysis(templateId))
        .then((body) => {
          if (alive) {
            setAnalysis(body);
            setProgress(null);
          }
        })
        .catch((err: unknown) => {
          // A stream that dies before the analysis exists must show a failure, not hang at 0%.
          if (alive) {
            setProgress(null);
            setFailure(err instanceof Error ? err.message : String(err));
          }
        });
    };

    if (jobId) {
      source = new EventSource(jobEventsUrl(jobId));
      source.onmessage = (event: MessageEvent<string>) => {
        let data: Partial<ProgressState> & { status?: string; error?: string };
        try {
          data = JSON.parse(event.data) as typeof data;
        } catch {
          source?.close();
          setProgress(null);
          setFailure("The progress stream returned an unreadable event.");
          return;
        }
        if (data.progress != null && data.stage && data.message) {
          setProgress({ stage: data.stage, message: data.message, progress: data.progress });
        }
        if (data.status === "done") {
          source?.close();
          load();
        } else if (data.status === "failed" || data.status === "cancelled") {
          source?.close();
          setProgress(null);
          setFailure(data.status === "cancelled" ? "Ingestion cancelled." : data.error ?? `job ${data.status}`);
        }
      };
      source.onerror = () => {
        // stream ends after the terminal event; if it died early fall back to a one-shot fetch
        source?.close();
        load();
      };
    } else {
      load();
    }
    return () => {
      alive = false;
      source?.close();
    };
  }, [templateId, jobId]);

  if (failure) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="max-w-[420px] text-center" title="Ingestion did not finish">
          <p className="text-sm text-ink-2" role="alert">
            {failure}
          </p>
          <div className="mt-3 flex justify-center gap-2">
            <Button variant="primary" onClick={() => window.location.reload()}>
              Retry
            </Button>
            <Button to="/" variant="ghost">
              Back to Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas" data-qa="ingest-progress">
        <Card className="w-[420px]" title="Analysing document">
          <Progress
            value={progress?.progress ?? 0}
            label={progress?.message ?? "Waiting for the server…"}
          />
          <p className="mt-2 text-xs text-ink-2">
            Stage: {progress?.stage ?? "queued"} · runs locally in a sandboxed worker
          </p>
          {jobId && (
            <div className="mt-3 flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                disabled={cancelRequested}
                onClick={() => {
                  setCancelRequested(true);
                  void cancelJob(jobId).catch((err: unknown) => {
                    setFailure(err instanceof Error ? err.message : String(err));
                  });
                }}
              >
                {cancelRequested ? "Cancelling…" : "Cancel ingestion"}
              </Button>
            </div>
          )}
        </Card>
      </div>
    );
  }

  return <AnalysisWorkspace templateId={templateId ?? analysis.template.id} analysis={analysis} />;
}

function AnalysisWorkspace({ templateId, analysis }: { templateId: string; analysis: AnalysisResponse }) {
  const template: Template = analysis.template;
  const live = useLiveStatus();
  const navigate = useNavigate();
  const pages = template.pages ?? [];
  const [pageIndex, setPageIndex] = useState(0);
  const [tab, setTab] = useState<"tree" | "issues">("tree");
  const [focused, setFocused] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function onEditContent() {
    setCreating(true);
    setCreateError(null);
    try {
      const document = await createDocument(templateId);
      void navigate(`/documents/${document.id}/manual`);
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : String(err));
      setCreating(false);
    }
  }

  const page = pages[Math.min(pageIndex, Math.max(pages.length - 1, 0))];
  const pageW = page?.size?.w ?? 612;
  const pageH = page?.size?.h ?? 792;
  const [zoom, setZoom] = useState(Math.round(Math.min(1.3, 820 / pageW) * 100));
  const z = zoom / 100;

  const children = flattenLayers(page?.nodes ?? []);
  const layerCount = pages.reduce((sum, p) => sum + flattenLayers(p.nodes ?? []).length, 0);
  const reviewItems = useMemo(() => template.reviewItems ?? [], [template.reviewItems]);
  const reviewByNode = useMemo(() => {
    const map = new Map<string, ReviewItem>();
    for (const item of reviewItems) for (const id of item.nodeIds ?? []) if (!map.has(id)) map.set(id, item);
    return map;
  }, [reviewItems]);

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={
          <Link to="/" aria-label="Back to Home" className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4">
            <Icon name="arrow_back" />
          </Link>
        }
        file={template.source?.fileName ?? template.name}
        fileMeta={`Template · ${pages.length} pages · ${layerCount} layers`}
        userName="Local user"
        userRole="This device"
        status={
          reviewItems.length > 0 ? (
            <span data-qa="analysis-status">
              <Tag tone="warning" icon={<Icon name="warning" className="text-[14px]" />}>
                Needs review ({reviewItems.length})
              </Tag>
            </span>
          ) : (
            <span data-qa="analysis-status">
              <Tag tone="info" icon={<Icon name="check_circle" className="text-[14px]" />}>
                Analysis complete
              </Tag>
            </span>
          )
        }
        actions={
          <Button
            variant="primary"
            size="sm"
            loading={creating}
            onClick={() => void onEditContent()}
            leading={<Icon name="edit" className="text-[16px]" />}
          >
            Edit content
          </Button>
        }
      />

      {createError && (
        <div className="px-6 pt-3">
          <Banner tone="error" title="Could not create the draft">
            <span className="text-sm">{createError}</span>
          </Banner>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-[300px] shrink-0 flex-col border-r border-border bg-card" data-qa="sidebar-left">
          <div className="flex h-12 items-center border-b border-border px-4">
            <span className="text-label-sm font-semibold tracking-wider text-ink-2 uppercase">
              Overlays ({children.length})
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <ul className="space-y-2">
              {children.map((node) => {
                const review = reviewByNode.get(node.id);
                return (
                  <li key={node.id}>
                    <button
                      type="button"
                      data-qa="analysis-item"
                      onClick={() => setFocused(node.id)}
                      className={`flex w-full items-start gap-2 rounded-md border px-3 py-2 text-left transition-colors ${
                        focused === node.id ? "border-brand bg-brand-tint/50" : "border-border bg-surface-2 hover:border-brand"
                      }`}
                    >
                      <span className={`mt-1 size-2.5 shrink-0 rounded-[3px] ${swatch(roleClassFor(node))}`} aria-hidden />
                      <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">{nodeLabel(node)}</span>
                      {review && <Icon name="warning" className="shrink-0 text-[14px] text-error" />}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
          <div className="border-t border-border p-3">
            <Button
              variant="primary"
              className="w-full"
              leading={<Icon name="check_circle" className="text-[16px]" />}
              onClick={() => setTab("issues")}
            >
              Review flagged items
            </Button>
          </div>
        </aside>

        <div className="relative min-w-0 flex-1 overflow-auto bg-canvas" data-qa="canvas-viewport">
          <div className="flex min-h-full items-start justify-center p-6 pb-24">
            <div className="relative" style={{ width: pageW * z, height: pageH * z }}>
              <div
                data-qa="canvas"
                className="relative overflow-hidden rounded-sm border border-border/80 bg-card shadow-l2"
                style={{ width: pageW * z, height: pageH * z }}
              >
                <img
                  data-qa="page-reference"
                  src={referenceUrl(templateId, pageIndex)}
                  alt={`Page ${pageIndex + 1} reference`}
                  className="absolute inset-0 h-full w-full object-contain"
                />
                {children.map((node) => {
                  const review = reviewByNode.get(node.id);
                  const roleClass = review ? "review" : roleClassFor(node);
                  return (
                    <OverlayBox
                      key={node.id}
                      x={node.bbox.x * z}
                      y={node.bbox.y * z}
                      w={node.bbox.w * z}
                      h={node.bbox.h * z}
                      roleClass={roleClass}
                      label={review ? `${nodeLabel(node)} · ${review.kind}` : nodeLabel(node)}
                      review={review?.suggestion ?? undefined}
                      selected={focused === node.id}
                      handleCount={focused === node.id ? 8 : 0}
                      handleClick={() => setFocused((f) => (f === node.id ? null : node.id))}
                      className="z-10"
                    />
                  );
                })}
              </div>
              <FloatingToolbar
                className="absolute top-4 left-1/2 z-20 -translate-x-1/2"
                zoom={{
                  value: zoom,
                  set: (v) => setZoom(Math.min(400, Math.max(25, v))),
                  step: (dir) => setZoom((v) => Math.min(400, Math.max(25, v + dir * 10))),
                  fit: () => setZoom(Math.round(Math.min(1.3, 820 / pageW) * 100)),
                }}
                page={{
                  label: `${pageIndex + 1} / ${Math.max(pages.length, 1)}`,
                  prev: pageIndex > 0 ? () => { setPageIndex((i) => i - 1); setFocused(null); } : undefined,
                  next:
                    pageIndex < pages.length - 1
                      ? () => { setPageIndex((i) => i + 1); setFocused(null); }
                      : undefined,
                }}
                toggles={[
                  { key: "layers", label: "Show layer tint", icon: "layers", checked: true, onChange: () => {} },
                ]}
              />
            </div>
          </div>
        </div>

        <aside className="flex w-[340px] shrink-0 flex-col border-l border-border bg-card" data-qa="sidebar-right">
          <div className="flex h-12 items-center gap-1 border-b border-border px-2" role="tablist" aria-label="Side panel">
            <TabBtn active={tab === "tree"} onClick={() => setTab("tree")} id="tab-tree" label={`Layer Tree · ${children.length}`} />
            <TabBtn active={tab === "issues"} onClick={() => setTab("issues")} id="tab-issues" label={`Issues (${reviewItems.length})`} />
          </div>

          {tab === "tree" ? (
            <div className="flex-1 overflow-y-auto" role="tabpanel" id="tabpanel-tree" aria-labelledby="tab-tree" data-qa="tabpanel-tree">
              {children.map((node) => (
                <button
                  key={node.id}
                  type="button"
                  data-qa="layer-row"
                  onClick={() => setFocused(node.id)}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-brand-tint/50"
                >
                  <Icon
                    name={node.locked ? "lock" : node.editable ? "edit" : "lock"}
                    className="shrink-0 text-[16px] text-ink-2"
                  />
                  <span className="min-w-0 flex-1 truncate text-sm text-ink">{nodeLabel(node)}</span>
                  <Tag tone={node.editable ? "success" : "neutral"}>{node.editable ? "editable" : "fixed"}</Tag>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex-1 space-y-3 overflow-y-auto p-3" role="tabpanel" id="tabpanel-issues" aria-labelledby="tab-issues" data-qa="tabpanel-issues">
              {reviewItems.length === 0 && (
                <Card className="p-3">
                  <p className="text-sm text-ink-2">No issues found — every layer passed its checks.</p>
                </Card>
              )}
              {groupReviews(reviewItems).map(([kind, items]) => (
                <Card key={kind} className="p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-ink">
                      {items.length}× {kind}
                    </p>
                    <Tag tone={severityTone(items)}>{severityLabel(items)}</Tag>
                  </div>
                  <ul className="mt-2 space-y-2">
                    {items.slice(0, 5).map((item) => (
                      <li key={item.id} className="text-xs text-ink-2">
                        <button
                          type="button"
                          className="text-left hover:text-ink"
                          onClick={() => {
                            const first = item.nodeIds?.[0];
                            if (first) {
                              setFocused(first);
                              const pageIdx = pages.findIndex((p) =>
                                flattenLayers(p.nodes ?? []).some((n) => n.id === first),
                              );
                              if (pageIdx >= 0) setPageIndex(pageIdx);
                            }
                          }}
                        >
                          {item.suggestion ?? item.id}
                          <span className="ml-1 tabular-nums">
                            ({Math.round((item.confidence ?? 0) * 100)}%)
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
          )}
        </aside>
      </div>

      <StatusBar
        left={{
          engine: "Engine ready",
          detail: `Confidence ${(analysis.confidence * 100).toFixed(1)}%`,
          ram: live?.ram ?? "—",
          parser: live?.parser ?? "Analysis: complete",
        }}
        privacyMode={live?.privacyMode ?? "No telemetry"}
        version={APP_VERSION}
      />
    </div>
  );
}

function roleClassFor(node: Node): RoleClass {
  if (OTHER_MEDIA_TYPES.has(node.type)) return node.type === "image" ? "media" : "shape";
  if (MEDIA_ROLES.has(node.role)) return "media";
  if (HEADING_ROLES.has(node.role)) return "headings";
  if (SHAPE_ROLES.has(node.role)) return "shape";
  return "text";
}

function nodeLabel(node: Node): string {
  if (node.name) return node.name;
  const role = ROLE_LABEL[node.role] ?? node.role;
  const text = (node.runs ?? []).map((run) => run.text).join(" ").replace(/\s+/g, " ").trim();
  return text ? `${role} · ${text.slice(0, 42)}` : role;
}

function groupReviews(items: ReviewItem[]): [string, ReviewItem[]][] {
  const groups = new Map<string, ReviewItem[]>();
  for (const item of items) {
    const list = groups.get(item.kind) ?? [];
    list.push(item);
    groups.set(item.kind, list);
  }
  return [...groups.entries()];
}

function severityTone(items: ReviewItem[]): TagTone {
  if (items.some((i) => i.severity === "error")) return "error";
  if (items.some((i) => i.severity === "warn")) return "warning";
  return "info";
}

function severityLabel(items: ReviewItem[]): string {
  return severityTone(items) === "error" ? "must fix" : severityTone(items) === "warning" ? "review" : "info";
}

function swatch(rc: RoleClass) {
  return {
    headings: "bg-ov-heading",
    text: "bg-ov-text",
    media: "bg-ov-media",
    shape: "bg-ov-shape",
    review: "bg-ov-review",
  }[rc];
}

function TabBtn({ active, onClick, label, id }: { active: boolean; onClick: () => void; label: string; id: string }) {
  return (
    <button
      id={id}
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      data-qa={id}
      className={
        active
          ? "rounded-md bg-brand-tint px-3 py-1.5 text-label-sm font-semibold text-brand"
          : "rounded-md px-3 py-1.5 text-label-sm font-medium text-ink-2 hover:bg-brand-tint/50"
      }
    >
      {label}
    </button>
  );
}
