import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { TooltipProvider } from "@templix/ui";
import { AnalysisLive } from "../src/screens/AnalysisLive";
import { HomeLive } from "../src/screens/HomeLive";
import { ManualLive } from "../src/screens/ManualLive";
import { DocumentsLive } from "../src/screens/DocumentsLive";
import * as api from "../src/lib/api";

// Live screens: no fixture identity/status, real API client, visible failure paths (F-03/F-11).

vi.mock("../src/lib/api", () => ({
  ensureSession: vi.fn(() => Promise.resolve()),
  listTemplates: vi.fn(),
  listDocuments: vi.fn(),
  uploadPdf: vi.fn(),
  getAnalysis: vi.fn(),
  getTemplate: vi.fn(),
  getDocument: vi.fn(),
  createDocument: vi.fn(),
  setSlot: vi.fn(),
  downloadExport: vi.fn(),
  cancelJob: vi.fn(),
  referenceUrl: (templateId: string, index: number) => `/reference/${templateId}/${index}`,
  jobEventsUrl: (jobId: string) => `/events/${jobId}`,
}));

vi.mock("../src/lib/useStatus", () => ({
  useLiveStatus: () => ({
    schemaVersion: 1,
    state: "ok",
    engine: "ready",
    version: "0.1.0",
    parser: "PDF Parser: PyMuPDF 1.26.0",
    ram: null,
    privacyMode: "No telemetry",
  }),
}));

const template = {
  id: "tpl-1",
  name: "Newsletter",
  version: 1,
  source: { fileName: "newsletter_2col.pdf" },
  pages: [
    {
      id: "page-1",
      size: { w: 612, h: 792 },
      nodes: [
        {
          id: "group-1",
          type: "group",
          children: [
            {
              id: "node-1",
              type: "text",
              role: "title",
              bbox: { x: 10, y: 10, w: 200, h: 40 },
              editable: true,
              runs: [{ text: "Quarterly update" }],
            },
          ],
        },
      ],
    },
  ],
  reviewItems: [
    {
      id: "font-001",
      kind: "font",
      nodeIds: ["node-1"],
      severity: "warn",
      suggestion: "Arial is unavailable; Inter will be used",
      confidence: 0.9,
    },
  ],
} as unknown as api.AnalysisResponse["template"];

const manualTemplate = {
  id: "tpl-1",
  name: "Newsletter",
  version: 1,
  source: { fileName: "newsletter.pdf" },
  pages: [
    {
      id: "page-1",
      size: { w: 612, h: 792 },
      referenceSha: "sha",
      nodes: [
        {
          id: "group-1",
          type: "group",
          children: [
            {
              id: "node-1",
              type: "text",
              role: "title",
              bbox: { x: 10, y: 10, w: 200, h: 40 },
              editable: true,
              provenance: { page: 0 },
              runs: [{ text: "Original headline" }],
            },
          ],
        },
      ],
    },
  ],
  slots: [
    {
      id: "slot-1",
      nodeIds: ["node-1"],
      label: "Headline",
      kind: "text",
      constraints: { maxChars: 80, maxLines: 2 },
    },
  ],
  reviewItems: [],
} as unknown as api.Template;

const manualDocument = {
  id: "doc-1",
  templateId: "tpl-1",
  templateVersion: 1,
  content: { values: { "slot-1": [{ text: "Original headline" }] } },
  status: "draft",
} as unknown as api.DocumentResponse;

beforeEach(() => {
  vi.mocked(api.ensureSession).mockResolvedValue();
  vi.mocked(api.listTemplates).mockResolvedValue([]);
  vi.mocked(api.listDocuments).mockResolvedValue([]);
  vi.mocked(api.getAnalysis).mockResolvedValue({ template, confidence: 0.93 });
  vi.mocked(api.getTemplate).mockResolvedValue(manualTemplate);
  vi.mocked(api.getDocument).mockResolvedValue(manualDocument);
  vi.mocked(api.createDocument).mockResolvedValue(manualDocument);
  vi.mocked(api.setSlot).mockResolvedValue({ document: manualDocument });
  vi.mocked(api.downloadExport).mockResolvedValue(new Blob(["%PDF-1.7"], { type: "application/pdf" }));
  vi.mocked(api.cancelJob).mockResolvedValue({ id: "job-1", kind: "ingest", status: "cancelled" });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

function renderHome() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <TooltipProvider>
        <Routes>
          <Route path="/" element={<HomeLive />} />
          <Route path="/templates/:templateId/analysis" element={<div />} />
        </Routes>
      </TooltipProvider>
    </MemoryRouter>,
  );
}

function renderAnalysis(entry: string | { pathname: string; state: unknown }) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <TooltipProvider>
        <Routes>
          <Route path="/templates/:templateId/analysis" element={<AnalysisLive />} />
          <Route path="/documents/:documentId/manual" element={<div data-testid="manual-route" />} />
        </Routes>
      </TooltipProvider>
    </MemoryRouter>,
  );
}

function renderManual() {
  return render(
    <MemoryRouter initialEntries={["/documents/doc-1/manual"]}>
      <TooltipProvider>
        <Routes>
          <Route path="/documents/:documentId/manual" element={<ManualLive />} />
          <Route path="/documents" element={<div data-testid="documents-route" />} />
        </Routes>
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("live Home", () => {
  it("shows the empty workspace, live status, and no fixture identity", async () => {
    renderHome();

    expect(await screen.findByText(/No templates yet/)).toBeTruthy();
    expect(screen.getAllByText(/PDF Parser: PyMuPDF 1.26.0/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Local user/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Shreya Iyer/)).toBeNull();
  });

  it("surfaces an unreachable server instead of hanging on Loading", async () => {
    vi.mocked(api.listTemplates).mockRejectedValue(new Error("connection refused"));
    renderHome();

    expect(await screen.findByText("Local server unreachable")).toBeTruthy();
    expect(screen.getByText("connection refused")).toBeTruthy();
  });

  it("sends the page-limit override with the selected PDF", async () => {
    const file = new File(["%PDF-1.7"], "many.pdf", { type: "application/pdf" });
    vi.mocked(api.uploadPdf).mockResolvedValue({ jobId: "job-1", templateId: "tpl-1" });
    const { container } = renderHome();
    await screen.findByText(/No templates yet/);

    fireEvent.click(screen.getByRole("checkbox", { name: /more than 50 pages/i }));
    const input = container.querySelector('[data-qa="upload-input"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(api.uploadPdf).toHaveBeenCalledWith(file, true));
  });
});

describe("live Analysis", () => {
  it("renders the layer tree and groups review items", async () => {
    renderAnalysis("/templates/tpl-1/analysis");

    expect(await screen.findByText(/Needs review \(1\)/)).toBeTruthy();
    expect(screen.getByText("Layer Tree · 1")).toBeTruthy();
    expect(screen.getAllByText(/Quarterly update/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("tab", { name: /^Issues/ }));
    expect(screen.getByText(/Arial is unavailable/)).toBeTruthy();
    expect(screen.getByText("(90%)")).toBeTruthy();
  });

  it("counts leaves inside nested groups", async () => {
    const leaf = {
      id: "node-1",
      type: "text",
      role: "title",
      bbox: { x: 10, y: 10, w: 200, h: 40 },
      editable: true,
      runs: [{ text: "Quarterly update" }],
    };
    const nested = {
      ...template,
      pages: [
        {
          ...(template.pages?.[0] as NonNullable<typeof template.pages>[number]),
          nodes: [
            {
              id: "group-outer",
              type: "group",
              children: [
                {
                  id: "group-inner",
                  type: "group",
                  children: [leaf, { ...leaf, id: "node-2" }],
                },
              ],
            },
          ],
        },
      ],
    } as unknown as api.AnalysisResponse["template"];
    vi.mocked(api.getAnalysis).mockResolvedValue({ template: nested, confidence: 0.93 });

    renderAnalysis("/templates/tpl-1/analysis");

    expect(await screen.findByText("Layer Tree · 2")).toBeTruthy();
  });

  it("shows a failure alert when the analysis cannot load", async () => {
    vi.mocked(api.getAnalysis).mockRejectedValue(new Error("Local server unreachable"));
    renderAnalysis("/templates/tpl-1/analysis");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Local server unreachable");
  });

  it("cancels an ingest and does not hang when the stream dies early", async () => {
    class FakeEventSource {
      static last: FakeEventSource | undefined;
      onmessage: ((event: MessageEvent<string>) => void) | null = null;
      onerror: (() => void) | null = null;
      close = vi.fn();
      constructor(public url: string) {
        FakeEventSource.last = this;
      }
    }
    vi.stubGlobal("EventSource", FakeEventSource);
    vi.mocked(api.getAnalysis).mockRejectedValue(new Error("analysis not ready"));

    renderAnalysis({ pathname: "/templates/tpl-1/analysis", state: { jobId: "job-1" } });

    fireEvent.click(await screen.findByRole("button", { name: "Cancel ingestion" }));
    expect(api.cancelJob).toHaveBeenCalledWith("job-1");

    FakeEventSource.last?.onerror?.();
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("analysis not ready");
  });

  it("creates a prefilled document and opens the manual editor", async () => {
    renderAnalysis("/templates/tpl-1/analysis");

    fireEvent.click(await screen.findByRole("button", { name: "Edit content" }));

    await waitFor(() => expect(api.createDocument).toHaveBeenCalledWith("tpl-1"));
    expect(await screen.findByTestId("manual-route")).toBeTruthy();
  });
});

describe("live manual editor", () => {
  it("loads prefilled text and autosaves an edit", async () => {
    renderManual();

    const field = await screen.findByDisplayValue("Original headline");
    fireEvent.change(field, { target: { value: "New headline" } });

    await waitFor(() => expect(api.setSlot).toHaveBeenCalledWith("doc-1", "slot-1", "New headline"), {
      timeout: 3000,
    });
    expect(await screen.findByText("Saved")).toBeTruthy();
  });

  it("downloads an exported PDF", async () => {
    renderManual();
    await screen.findByDisplayValue("Original headline");

    fireEvent.click(screen.getByRole("button", { name: /Export PDF/ }));

    await waitFor(() => expect(api.downloadExport).toHaveBeenCalledWith("doc-1"));
  });
});

describe("live documents", () => {
  it("lists drafts with their template names", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([
      {
        id: "doc-1",
        templateId: "tpl-1",
        templateVersion: 1,
        status: "draft",
        updatedAt: "2026-01-01T00:00:00Z",
      },
    ]);
    vi.mocked(api.listTemplates).mockResolvedValue([
      {
        id: "tpl-1",
        name: "Newsletter",
        version: 1,
        updatedAt: "2026-01-01T00:00:00Z",
        pageCount: 1,
        layerCount: 1,
        status: "ready",
      },
    ]);

    render(
      <MemoryRouter>
        <TooltipProvider>
          <DocumentsLive />
        </TooltipProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Newsletter")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open" })).toBeTruthy();
  });
});
