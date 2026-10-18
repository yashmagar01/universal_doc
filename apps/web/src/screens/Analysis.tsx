import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import {
  Button,
  Card,
  FloatingToolbar,
  Icon,
  OverlayBox,
  StatusBar,
  Tag,
  WorkspaceTopBar,
  type IconName,
  type TagTone,
} from "@templix/ui";
import { APP_VERSION } from "../lib/version";
import { fixtureAnalysis, PAGE_H, PAGE_SCALE, PAGE_W, type DemoNode, type DemoRole } from "../fixtures/demo";

const roleClass: Record<DemoRole, "headings" | "text" | "media" | "shape" | "review"> = {
  title: "headings",
  heading1: "headings",
  heading2: "headings",
  body: "text",
  caption: "text",
  image: "media",
  quote: "review",
  footer: "shape",
};

export function AnalysisScreen() {
  const { templateId } = useParams();
  const a = fixtureAnalysis;
  const [tab, setTab] = useState<"tree" | "issues">("tree");
  const [focused, setFocused] = useState<string | null>(null);
  const [zoom, setZoom] = useState(PAGE_SCALE * 100);

  const treeItems = useMemo(() => a.tree.groups.flatMap((g) => g.layers.map((l) => ({ ...l, group: g.name }))), [a]);
  const issueCount = Object.values(a.reviewCounts).reduce((s, x) => s + x, 0);

  if (templateId !== a.templateId) {
    return (
      <div className="grid min-h-dvh place-items-center bg-canvas">
        <Card className="max-w-[380px] text-center" title="Unknown template">
          <p className="text-sm text-ink-2">This M0 build ships a single demo analysis.</p>
          <Button to="/" variant="primary">Back to Home</Button>
        </Card>
      </div>
    );
  }

  const z = zoom / 100;
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <WorkspaceTopBar
        back={<Link to="/" aria-label="Back to Home" className="inline-flex size-9 items-center justify-center rounded-full text-ink-2 hover:bg-black/4"><Icon name="arrow_back" /></Link>}
        file={a.fileName}
        fileMeta={`Template · ${a.pages} pages · ${a.layerCount} layers`}
        status={<Tag tone="info" icon={<Icon name="check_circle" className="text-[14px]" />}>Analysis complete</Tag>}
        actions={
          <>
            <Button variant="ghost" size="sm" leading={<Icon name="add" className="text-[16px]" />}>Add page</Button>
            <Button
              to={`/templates/${a.templateId}/mode`}
              variant="primary"
              size="sm"
              trailing={<Icon name="arrow_forward" className="text-[16px]" />}
            >
              Next: Choose Mode
            </Button>
          </>
        }
      />

      <div className="flex min-h-0 flex-1">
        {/* Left: overlay/layer list */}
        <aside className="flex w-[300px] shrink-0 flex-col border-r border-border bg-card" data-qa="sidebar-left">
          <div className="flex h-12 items-center border-b border-border px-4">
            <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-2">
              Overlays ({a.nodes.length})
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            <ul className="space-y-2">
              {a.nodes.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    data-qa="analysis-item"
                    onClick={() => setFocused(n.id)}
                    className={`flex w-full items-start gap-2 rounded-md border px-3 py-2 text-left transition-colors ${
                      focused === n.id ? "border-brand bg-brand-tint/50" : "border-border bg-surface-2 hover:border-brand"
                    }`}
                  >
                    <span className={`mt-1 size-2.5 shrink-0 rounded-[3px] ${swatch(roleClass[n.role])}`} aria-hidden />
                    <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">{n.label}</span>
                    {n.review && <Icon name="warning" className="text-[14px] shrink-0 text-error" />}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="border-t border-border p-3">
            <Button variant="primary" className="w-full" leading={<Icon name="check_circle" className="text-[16px]" />}>
              Done reviewing
            </Button>
            <Button variant="ghost" className="mt-2 w-full">Pull template</Button>
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
                {a.nodes.map((n) => (
                  <PageNode key={n.id} node={n} z={z} />
                ))}
                {/* overlay boxes on top of schematic content */}
                {a.nodes.map((n) => (
                  <OverlayBox
                    key={`o-${n.id}`}
                    x={n.bbox.x * z}
                    y={n.bbox.y * z}
                    w={n.bbox.w * z}
                    h={n.bbox.h * z}
                    roleClass={roleClass[n.role]}
                    label={n.review ? `${n.label} · ${n.review}` : n.label}
                    review={n.review}
                    selected={focused === n.id}
                    handleCount={focused === n.id ? 8 : 0}
                    handleClick={() => setFocused((f) => (f === n.id ? null : n.id))}
                    className="z-10"
                  />
                ))}
              </div>
              <FloatingToolbar
                className="absolute top-4 left-1/2 -translate-x-1/2 z-20"
                zoom={{
                  value: zoom,
                  set: (v) => setZoom(Math.min(400, Math.max(25, v))),
                  step: (dir) => setZoom((v) => Math.min(400, Math.max(25, v + dir * 10))),
                  fit: () => setZoom(Math.round(PAGE_SCALE * 100)),
                }}
                page={{ label: `1 / ${a.pages}` }}
                toggles={[
                  { key: "grid", label: "Show grid", icon: "grid_4x4", checked: false, onChange: () => {} },
                  { key: "layers", label: "Show layer tint", icon: "layers", checked: true, onChange: () => {} },
                ]}
              />
            </div>
          </div>
        </div>

        {/* Right: tabs */}
        <aside className="flex w-[340px] shrink-0 flex-col border-l border-border bg-card" data-qa="sidebar-right">
          <div className="flex h-12 items-center gap-1 border-b border-border px-2" role="tablist" aria-label="Side panel">
            <TabBtn active={tab === "tree"} onClick={() => setTab("tree")} id="tab-tree" label={`Layer Tree · ${treeItems.length}`} />
            <TabBtn active={tab === "issues"} onClick={() => setTab("issues")} id="tab-issues" label={`Issues (${issueCount})`} />
          </div>

          {tab === "tree" ? (
            <div className="flex-1 overflow-y-auto" role="tabpanel" id="tabpanel-tree" aria-labelledby="tab-tree">
              {a.tree.groups.map((g) => (
                <div key={g.name} className="border-b border-border/60 pb-2">
                  <div className="flex h-9 items-center gap-2 px-3 text-label-sm font-semibold uppercase tracking-wider text-ink-2">
                    <Icon name="folder_outlined" className="text-[16px]" />
                    {g.name}
                  </div>
                  {g.layers.map((l) => (
                    <LayerRowBtn
                      key={l.id}
                      name={l.name}
                      state={"state" in l ? l.state : "editable"}
                      reason={"reason" in l ? l.reason : undefined}
                      onClick={() => setFocused(l.id)}
                    />
                  ))}
                </div>
              ))}
              <p className="px-3 py-3 text-xs text-ink-2">
                Page 2 · {a.page2Layers} layers (masthead continuity: locked title block)
              </p>
            </div>
          ) : (
            <div className="flex-1 space-y-3 overflow-y-auto p-3" role="tabpanel" id="tabpanel-issues" aria-labelledby="tab-issues">
              {Object.entries(a.reviewCounts).map(([kind, count]) => (
                <Card key={kind} className="p-3">
                  <p className="text-sm font-medium text-ink">{count}× {kind}</p>
                  <p className="mt-1 text-xs text-ink-2">
                    {kind === "low-contrast text"
                      ? "Text colors fall below the 4.5:1 readability target. Auto-repairs propose darker shades."
                      : "These vector groups need a label until verified."}
                  </p>
                  <Button variant="secondary" size="sm" className="mt-2" leading={<Icon name="auto_fix_high" className="text-[16px]" />}>
                    Auto-repair
                  </Button>
                </Card>
              ))}
              <Card className="p-3">
                <p className="text-sm font-semibold text-ink">Rule summary</p>
                <ul className="mt-1 space-y-1 text-xs text-ink-2">
                  <li>Contrast policy: 4.5:1 minimum pass/fail</li>
                  <li>Line length: 2-line cap on locked headlines</li>
                  <li>Overflow: locked frame height honored</li>
                </ul>
              </Card>
            </div>
          )}

          <div className="border-t border-border p-3">
            <Button to={`/templates/${a.templateId}/mode`} variant="primary" className="w-full">Next: Choose Mode</Button>
          </div>
        </aside>
      </div>

      <StatusBar
        left={{ engine: "Engine ready", detail: `Fidelity ${(a.fidelity.overall * 100).toFixed(1)}%`, ram: "—", parser: "Analysis: complete" }}
        privacyMode="No telemetry"
        version={APP_VERSION}
      />
    </div>
  );
}

function swatch(rc: "headings" | "text" | "media" | "shape" | "review") {
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

function LayerRowBtn({
  name,
  state,
  reason,
  onClick,
}: {
  name: string;
  state: "editable" | "fixed" | "slot" | "review";
  reason?: string;
  onClick: () => void;
}) {
  const icon: IconName = state === "review" ? "warning" : state === "fixed" ? "lock" : state === "slot" ? "image" : "edit";
  const tone: TagTone = state === "review" ? "error" : state === "slot" ? "info" : state === "fixed" ? "neutral" : "success";
  const stateLabel = state === "review" && reason ? `${state} · ${reason}` : state;
  return (
    <button
      type="button"
      onClick={onClick}
      data-qa="layer-row"
      className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-brand-tint/50"
    >
      <Icon name={icon} className="shrink-0 text-[16px] text-ink-2" />
      <span className="min-w-0 flex-1 truncate text-sm text-ink">{name}</span>
      <Tag tone={tone}>{stateLabel}</Tag>
    </button>
  );
}

/** schematic page content so overlay boxes sit on real (fixture) content */
function PageNode({ node, z }: { node: DemoNode; z: number }) {
  const style: React.CSSProperties = {
    position: "absolute",
    left: node.bbox.x * z,
    top: node.bbox.y * z,
    width: node.bbox.w * z,
    height: node.bbox.h * z,
  };
  const clamp = (px: number) => Math.max(7, px * z);

  if (node.role === "image") {
    return (
      <div style={style} className="grid place-items-center gap-1 bg-brand-tint/60 p-2 text-center">
        <Icon name="image" className="text-brand" />
        <p className="text-[10px] font-medium leading-tight text-brand">{node.text}</p>
      </div>
    );
  }
  if (node.role === "quote") {
    return (
      <div style={style} className="flex items-center bg-brand-tint/50 p-3">
        <p style={{ fontSize: clamp(13) }} className="font-semibold text-error">{node.text}</p>
      </div>
    );
  }
  if (node.role === "title") {
    return (
      <div style={style} className="flex items-center">
        <p style={{ fontSize: clamp(36) }} className="font-extrabold tracking-tight text-ink">{node.text}</p>
      </div>
    );
  }
  if (node.role === "heading1") {
    return (
      <div style={style} className="flex items-center">
        <p style={{ fontSize: clamp(22) }} className="font-semibold leading-tight text-ink">{node.text}</p>
      </div>
    );
  }
  if (node.role === "heading2") {
    return (
      <div style={style} className="flex items-center">
        <p style={{ fontSize: clamp(12) }} className="font-medium uppercase tracking-wider text-brand">{node.text}</p>
      </div>
    );
  }
  return (
    <div style={style}>
      <p style={{ fontSize: clamp(node.role === "footer" ? 10 : 13) }} className={`leading-snug ${node.role === "footer" ? "pt-1 text-center text-ink-2" : "text-ink-2"}`}>
        {node.text}
      </p>
    </div>
  );
}
