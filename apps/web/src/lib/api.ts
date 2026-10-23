import type { Document as DocumentRecord, ReviewItem, Template } from "@templix/doc-schema";

/** Thin live-API client (§11). Session bootstrap: `?token=` (one-time URL) or VITE_TEMPLIX_TOKEN. */

const BASE = "/api/v1";

export interface TemplateSummary {
  id: string;
  name: string;
  version: number;
  updatedAt: string;
  pageCount: number;
  layerCount: number;
  status: "ready" | "needs-review";
}

export interface AnalysisResponse {
  template: Template;
  confidence: number;
}

export type DocumentResponse = DocumentRecord;

export interface DocumentSummary {
  id: string;
  templateId: string;
  templateVersion: number;
  status: string;
  updatedAt: string;
}

/** Live system facts from GET /status (FR-SYS-02). */
export interface StatusResponse {
  schemaVersion: number;
  state: string;
  engine: string;
  version: string;
  parser: string;
  ram: string | null;
  privacyMode: string;
}

export interface JobStatus {
  id: string;
  kind: string;
  status: "queued" | "running" | "done" | "failed" | "cancelled";
  error?: string | null;
}

export interface IngestAccepted {
  jobId: string;
  templateId: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function responseError(response: Response): Promise<ApiError> {
  let detail = `${response.status}`;
  try {
    const body: unknown = await response.json();
    const data = (typeof body === "object" && body !== null ? body : {}) as {
      hint?: unknown;
      detail?: unknown;
    };
    const message = data.hint ?? data.detail;
    if (typeof message === "string") detail = message;
    else if (message !== undefined) detail = JSON.stringify(message);
  } catch {
    /* non-JSON error body: keep the status text */
  }
  return new ApiError(response.status, detail);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { credentials: "same-origin", ...init });
  if (!response.ok) throw await responseError(response);
  return (await response.json()) as T;
}

let session: Promise<void> | null = null;

/** Exchange the one-time token for the session cookie, once per app load. */
export function ensureSession(): Promise<void> {
  if (session === null) {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token") ?? import.meta.env.VITE_TEMPLIX_TOKEN;
    if (!token) {
      session = Promise.resolve();
    } else {
      session = fetch(`${BASE}/session`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-Templix-Launch-Token": token },
      }).then((response) => {
        if (!response.ok) {
          session = null;
          throw new ApiError(response.status, "session rejected");
        }
        params.delete("token");
        const qs = params.toString();
        window.history.replaceState(null, "", window.location.pathname + (qs ? `?${qs}` : ""));
      });
    }
  }
  return session;
}

export const getStatus = () => requestJson<StatusResponse>("/status");
export const listTemplates = () => requestJson<TemplateSummary[]>("/templates");
export const getAnalysis = (templateId: string) => requestJson<AnalysisResponse>(`/templates/${templateId}/analysis`);
export const getTemplate = (templateId: string) => requestJson<Template>(`/templates/${templateId}`);
export const listDocuments = () => requestJson<DocumentSummary[]>("/documents");
export const getDocument = (documentId: string) => requestJson<DocumentResponse>(`/documents/${documentId}`);
export const createDocument = (templateId: string) =>
  requestJson<DocumentResponse>("/documents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ templateId }),
  });
export const setSlot = (documentId: string, slotId: string, text: string) =>
  requestJson<{ document: DocumentResponse }>(`/documents/${documentId}/ops`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ops: [{ kind: "set_slot", slotId, value: [{ text }] }] }),
  });
export async function downloadExport(documentId: string): Promise<Blob> {
  const response = await fetch(`${BASE}/documents/${documentId}/export.pdf`, {
    credentials: "same-origin",
  });
  if (!response.ok) throw await responseError(response);
  return response.blob();
}
export const getJob = (jobId: string) => requestJson<JobStatus>(`/jobs/${jobId}`);
export const cancelJob = (jobId: string) =>
  requestJson<JobStatus>(`/jobs/${jobId}/cancel`, { method: "POST" });
export const referenceUrl = (templateId: string, pageIndex: number) =>
  `${BASE}/templates/${templateId}/pages/${pageIndex}/reference.png`;
export const jobEventsUrl = (jobId: string) => `${BASE}/jobs/${jobId}/events`;

export async function uploadPdf(file: File, allowManyPages = false): Promise<IngestAccepted> {
  const form = new FormData();
  form.append("file", file);
  if (allowManyPages) form.append("allowManyPages", "true");
  return requestJson<IngestAccepted>("/templates/ingest", { method: "POST", body: form });
}

export type { ReviewItem, Template };
