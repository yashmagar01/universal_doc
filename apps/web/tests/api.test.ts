import { afterEach, describe, expect, it, vi } from "vitest";
import { cancelJob, getStatus, uploadPdf } from "../src/lib/api";

function ok(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("live API client", () => {
  it("omits the page-limit override unless asked", async () => {
    const fetchMock = vi.fn<(input: string, init?: RequestInit) => Promise<Response>>();
    fetchMock.mockResolvedValue(ok({ jobId: "j1", templateId: "t1" }, 202));
    vi.stubGlobal("fetch", fetchMock);

    await uploadPdf(new File(["%PDF-1.7"], "doc.pdf", { type: "application/pdf" }));

    const form = fetchMock.mock.calls[0]?.[1]?.body as FormData;
    expect(form.get("allowManyPages")).toBeNull();
  });

  it("sends the page-limit override when enabled", async () => {
    const fetchMock = vi.fn<(input: string, init?: RequestInit) => Promise<Response>>();
    fetchMock.mockResolvedValue(ok({ jobId: "j2", templateId: "t2" }, 202));
    vi.stubGlobal("fetch", fetchMock);

    await uploadPdf(new File(["%PDF-1.7"], "doc.pdf", { type: "application/pdf" }), true);

    const form = fetchMock.mock.calls[0]?.[1]?.body as FormData;
    expect(form.get("allowManyPages")).toBe("true");
  });

  it("cancels through the job endpoint", async () => {
    const fetchMock = vi.fn<(input: string, init?: RequestInit) => Promise<Response>>();
    fetchMock.mockResolvedValue(ok({ id: "job-1", kind: "ingest", status: "cancelled" }));
    vi.stubGlobal("fetch", fetchMock);

    await cancelJob("job-1");

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/jobs/job-1/cancel");
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("POST");
  });

  it("surfaces the problem hint instead of the raw detail", async () => {
    const fetchMock = vi.fn<(input: string, init?: RequestInit) => Promise<Response>>();
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          type: "about:blank",
          title: "Not Found",
          status: 404,
          detail: "template not found",
          code: "not_found",
          hint: "Template not found. Pick another one.",
        }),
        { status: 404, headers: { "Content-Type": "application/problem+json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getStatus()).rejects.toThrow("Template not found. Pick another one.");
  });

  it("keeps an unavailable RAM read honest", async () => {
    const fetchMock = vi.fn<(input: string, init?: RequestInit) => Promise<Response>>();
    fetchMock.mockResolvedValue(
      ok({
        schemaVersion: 1,
        state: "ok",
        engine: "ready",
        version: "0.1.0",
        parser: "PDF Parser: PyMuPDF 1.26.0",
        ram: null,
        privacyMode: "No telemetry",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const status = await getStatus();

    expect(status.ram).toBeNull();
    expect(status.privacyMode).toBe("No telemetry");
  });
});
