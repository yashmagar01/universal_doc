import type { ActivityCount, ProfileInfo, ProviderState, StatusBarContent } from "../lib/types";

/**
 * DEV FIXTURE DATA ONLY (design.md §12-22, FR-HOME-*, NFR-FID-07).
 * All numbers live here as data — screens derive display values from them, never hard-code.
 * In live mode (M1+) every field is replaced by server data.
 */

export const fixtureUser: ProfileInfo = {
  name: "Shreya Iyer",
  role: "Editor",
  team: "Magazine & Newsletter Team",
  orgChip: "Student Publishing Board",
};

export const fixtureCounts: ActivityCount = {
  templatesManaged: 6,
  documentsCreated: 48,
  storageUsed: "124 MB",
};

export const fixtureProvider: ProviderState = {
  id: null,
  label: "",
  connected: false,
};

export const fixtureStatus: StatusBarContent = {
  ram: "—",
  parser: "PDF Parser: v0 (fixture mode)",
  privacyMode: "No telemetry",
  user: fixtureUser,
};

export interface DemoTemplate {
  id: string;
  name: string;
  kind: "newsletter" | "report" | "flyer";
  layers: number;
  pages: number;
  lastUsed: string;
  status: "ready" | "needs-review" | "processing" | "failed";
  thumbPattern: "masthead" | "columns" | "reviewed" | "split";
}

export const fixtureTemplates: DemoTemplate[] = [
  { id: "t_newsletter", name: "Campus Monthly Newsletter", kind: "newsletter", layers: 12, pages: 2, lastUsed: "3 days ago", status: "ready", thumbPattern: "masthead" },
  { id: "t_financial", name: "Annual Financial & Activities Report", kind: "report", layers: 18, pages: 6, lastUsed: "yesterday", status: "ready", thumbPattern: "columns" },
  { id: "t_exec", name: "Executive Committee Weekly", kind: "newsletter", layers: 8, pages: 1, lastUsed: "1 hr ago", status: "needs-review", thumbPattern: "reviewed" },
  { id: "t_orientation", name: "Orientation Week Guide & Map", kind: "flyer", layers: 15, pages: 3, lastUsed: "2 weeks ago", status: "ready", thumbPattern: "split" },
];

export interface DemoDocSummary {
  id: string;
  title: string;
  updated: string;
  status: "in-progress-ai" | "in-progress-manual" | "completed";
  exported: boolean;
}

export const fixtureDocuments: DemoDocSummary[] = [
  { id: "d_march", title: "March Newsletter - Draft v2", updated: "2 hours ago", status: "in-progress-ai", exported: false },
  { id: "d_budget", title: "Q1 Budget Summary - Final", updated: "6 days ago", status: "completed", exported: true },
  { id: "d_oweek", title: "O-Week Flyer - Batch 1", updated: "4 days ago", status: "completed", exported: true },
];

/** ---- Analysis screen (Document Layer Analysis) ---- */

export type DemoRole = "title" | "heading1" | "heading2" | "body" | "caption" | "image" | "quote" | "footer";
export type RoleClass = "headings" | "text" | "media" | "shape" | "review";

export interface DemoNode {
  id: string;
  role: DemoRole;
  label: string;
  bbox: { x: number; y: number; w: number; h: number };
  text?: string;
  review?: string;
  contrastRatio?: string;
}

export const PAGE_W = 612;
export const PAGE_H = 792;
/** default canvas fit-to-width zoom for the 1333×900 reference viewport */
export const PAGE_SCALE = 0.85;

export const fixtureAnalysis = {
  templateId: "t_newsletter",
  fileName: "Campus_Monthly_Newsletter_Mar2025.pdf",
  pages: 2,
  layerCount: 24,
  confidence: 0.92,
  reviewCounts: { "low-contrast text": 2, "vector shape groups": 2 } as Record<string, number>,
  orientation: "Letter (Portrait)",
  running: false,
  nodes: [
    { id: "n_title", role: "title", label: "Title: Campus Chronicle", bbox: { x: 48, y: 64, w: 516, h: 48 }, text: "CAMPUS CHRONICLE" },
    { id: "n_kicker", role: "heading2", label: "Subtitle Block", bbox: { x: 48, y: 124, w: 516, h: 40 }, text: "STUDENT AFFAIRS & LEADERSHIP BRIEFING — March 2025 · Vol. 14 · Issue 4", review: "overlap check" },
    { id: "n_lead", role: "heading1", label: "Lead Story", bbox: { x: 48, y: 188, w: 380, h: 64 }, text: "New Local AI Laboratories Open for Collaborative Research Projects" },
    { id: "n_photo", role: "image", label: "Story Photo [Image]", bbox: { x: 48, y: 264, w: 246, h: 150 }, text: "Students at the newly commissioned local technology laboratory" },
    { id: "n_quote", role: "quote", label: "Callout Quote", bbox: { x: 310, y: 264, w: 254, h: 150 }, text: '“Empowering student voices through private and uncompromised local infrastructure.”', review: "Low contrast", contrastRatio: "2.8:1" },
    { id: "n_body1", role: "body", label: "Column 1 Body", bbox: { x: 48, y: 428, w: 246, h: 284 }, text: "University administration has officially ratified the digital privacy initiative, dedicating campus nodes strictly to private local processing. Students working on sensitive research theses and institutional datasets can now execute extraction routines without external dependencies." },
    { id: "n_body2", role: "body", label: "Column 2 Body", bbox: { x: 310, y: 428, w: 254, h: 284 }, text: "Regular training orientations take place Tuesdays and Thursdays in Hall C. Templates created locally are fully exportable to standard Open Document specifications, making formatting updates instantaneous." },
    { id: "n_footer", role: "footer", label: "Issue Footer", bbox: { x: 48, y: 728, w: 516, h: 24 }, text: "Campus Chronicle • Student Affairs Publication Office" },
  ] as DemoNode[],
  page2Layers: 6,
  tree: {
    groups: [
      { name: "Header Container", layers: [{ id: "n_title", name: "Title: Campus Chronicle", roleLabel: "Heading 1", state: "editable" as const }, { id: "k1", name: "March 2025 · Issue 4", roleLabel: "Label", state: "fixed" as const }, { id: "k2", name: "Divider Line (1.5pt)", roleLabel: "Shape", state: "fixed" as const }] },
      { name: "Main Content", layers: [{ id: "n_lead", name: "Lead Story Headline", roleLabel: "Heading 1", state: "editable" as const }, { id: "n_photo", name: "Story Photo [Image]", roleLabel: "Image", state: "slot" as const }, { id: "n_quote", name: "Callout Quote", roleLabel: "Quote", state: "review" as const, reason: "Low Contrast" }] },
    ],
  },
  fidelity: { overall: 0.975, pages: [0.981, 0.964] },
};

/** ---- Manual editor ---- */

export interface DemoSlot {
  id: string;
  label: string;
  kind: "text" | "richtext" | "image" | "date" | "link";
  value: string;
  maxChars?: number;
  maxWords?: number;
  state?: "ok" | "near" | "over";
}

export interface RepeaterInstance {
  id: string;
  title: string;
  author: string;
  words: number;
}

export interface DemoSection {
  id: string;
  label: string;
  status: { label: string; tone: "success" | "info" | "neutral" | "warning" };
  slots: DemoSlot[];
  repeater?: { id: string; max: number; instances: RepeaterInstance[] };
}

export const fixtureManualDoc = {
  documentId: "d_march",
  title: "Campus Chronicle - March Draft",
  pageNum: 1,
  pageCount: 2,
  autosaved: true,
  fidelity: fixtureAnalysis.fidelity.overall,
  sections: [
    {
      id: "s_cover",
      label: "Cover & Masthead",
      status: { label: "Complete", tone: "success" as const },
      slots: [
        { id: "sl_title", label: "Masthead Title", kind: "text", value: "CAMPUS CHRONICLE", maxChars: 24 } as DemoSlot,
        { id: "sl_issue", label: "Issue Line", kind: "text", value: "March 2025 · Vol. 14 · Issue 4", maxChars: 40 } as DemoSlot,
      ],
    },
    {
      id: "s_lead",
      label: "Lead Editorial Story",
      status: { label: "Active sync", tone: "info" as const },
      slots: [
        { id: "sl_headline", label: "Story Headline", kind: "text", value: "New Local AI Laboratories Open for Collaborative Research Projects", maxChars: 65 } as DemoSlot,
        { id: "sl_byline", label: "Author / Byline", kind: "text", value: "By Priya Nair · Student Affairs Desk" } as DemoSlot,
        { id: "sl_photo", label: "Feature Image", kind: "image", value: "lab_opening_day.jpg · 2.4 MB (300×200 crop)" } as DemoSlot,
        { id: "sl_body", label: "Story Body Copy", kind: "richtext", value: "182 words · 2 paragraphs — fits the locked frame at 100% scale", maxWords: 200 } as DemoSlot,
      ],
    },
    {
      id: "s_articles",
      label: "Articles & Highlights",
      status: { label: "3 Articles", tone: "neutral" as const },
      repeater: {
        id: "rp_articles",
        max: 3,
        instances: [
          { id: "i1", title: "Robotics Club Secures Grant", author: "Marcus Chen", words: 48 },
          { id: "i2", title: "Library Extends Weeknight Hours", author: "Fatima Rana", words: 63 },
          { id: "i3", title: "Placement Drive: Nine Recruiters", author: "Aditi Kulkarni", words: 55 },
        ],
      },
      slots: [] as DemoSlot[],
    },
  ] as DemoSection[],
  warnings:
    [
      { id: "w1", kind: "line-length", slot: "sl_headline", text: "Headline wraps to 2 lines at locked size (65 chars max per line policy)" },
    ] as { id: string; kind: string; slot: string; text: string }[],
  rulesPassed: { passed: 5, kinds: ["margins", "font hierarchy", "contrast"] },
};

/** ---- Mode picker ---- */
export const fixtureMode = {
  templateId: "t_newsletter",
  fileName: "Campus_Monthly_Newsletter_Mar2025.pdf",
  pages: 2,
  layers: 24,
  provider: fixtureProvider,
};

/** ---- AI assist ---- */
export const fixtureAi = {
  documentId: "d_march",
  providerLabel: "Anthropic",
  modelId: "claude-sonnet-4-5",
  latencyMs: 412,
  step: 3,
  stepTotal: 7,
  stepLabel: "Lead Story Headline",
  stepPct: 45,
  messages: [
    { id: "m1", side: "assistant", text: "Welcome back. Your template has 7 sections with editable slots. We'll go through them one at a time." },
    { id: "m2", side: "assistant", text: "Section: Cover & Masthead — slot: Masthead Title.", quote: "CAMPUS CHRONICLE" },
    { id: "m3", side: "user", text: "Keep as is" },
    { id: "m4", side: "assistant", text: "Section: Lead Editorial Story — slot: Story Headline. Here is a draft:" },
  ],
  proposals: {
    pending: 3,
    accepted: 1,
    fitsAll: true,
    cards: [
      { id: "p1", slot: "Story Headline", meta: "Page 1 · Lead Story", counter: "58 / 65 max chars", original: "New Local AI Laboratories Open for Collaborative Research Projects", proposal: "Campus Gets Dedicated AI Labs for Student Research", target: "2 lines exact", tone: "safe" as const },
      { id: "p2", slot: "Deadline", meta: "Page 1 · Notice", counter: "24 / 40 max chars", original: "Submit applications by April 20, 2025", proposal: "Friday, May 2 at 11:59 PM", target: "date field", tone: "safe" as const },
      { id: "p3", slot: "Column 1 Body", meta: "Page 1 · Body", counter: "182 / 200 words", original: "University administration has officially ratified…", proposal: "University administration has formally ratified…", target: "flow: 2 columns", tone: "warn" as const },
    ],
  },
  slotHeight: { current: 58, max: 60 },
};

/** ---- Settings ---- */
export interface DemoEngine {
  id: string;
  name: string;
  tag: string;
  desc: string;
  configured: boolean;
  comingSoon?: boolean;
}

export const fixtureSettings = {
  configuredCount: 0,
  engines: [
    { id: "openai", name: "OpenAI", tag: "Cloud API", desc: "GPT-family models for drafting and editing.", configured: false },
    { id: "anthropic", name: "Anthropic", tag: "Cloud API", desc: "Claude-family models for drafting and editing.", configured: false },
    { id: "google", name: "Google (Gemini)", tag: "Cloud API", desc: "Gemini models via the unified SDK.", configured: false },
    { id: "openai_compat", name: "OpenAI-compatible endpoint", tag: "Cloud API", desc: "OpenRouter, Groq, Together, vLLM or any compatible host.", configured: false },
    { id: "ollama", name: "Ollama / Local", tag: "Coming soon", desc: "Run models on your own computer in a later release.", configured: false, comingSoon: true },
  ] as DemoEngine[],
  localRuntime: { server: "Running · 127.0.0.1", cache: "36 MB" },
};
