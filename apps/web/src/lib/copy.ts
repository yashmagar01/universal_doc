/**
 * Exact UI strings from docs/design.md §9 (copy deck). Never inline privacy/quality claims.
 * Forbidden phrases are lint-enforced (see eslint rules copy-lint).
 */
export const copy = {
  badge: {
    local: "LOCAL APP",
    localTooltip: "Templix runs on this computer. Your files, templates and keys are stored here.",
  },
  privacy: {
    cardNone: {
      title: "Everything stays on this device",
      body: "Templix hasn't been connected to any AI service. Analysis, editing and export all run on this computer.",
    },
    cardProvider: (provider: string) => ({
      title: "You're in control of what is shared",
      body: `Analysis, manual editing and export run on this computer. If you use AI Assist, the text of the section you're working on is sent to ${provider}. Templix asks before the first send and keeps a log you can review.`,
    }),
    modeManual: "Manual Edit runs entirely on this computer. Nothing is sent anywhere.",
    modeAi: (provider: string) =>
      `AI Assist sends the text of the section you're working on — not your whole document — to ${provider}. Your API key stays in this computer's keychain.`,
    vlm: (pages: number, provider: string, model: string) =>
      `To label this document's layout, Templix will send images of ${pages} pages to ${provider} (${model}).`,
    indicatorNone: "No data leaves this device",
    indicatorCloud: (provider: string) => `Sends text to ${provider}`,
  },
  indicator: {
    staysLocal: "No data leaves this device",
    cloud: (provider: string) => `Sends text to ${provider}`,
  },
  settings: {
    dataBoundary:
      "Templix stores your documents, templates and keys on this computer. Reading your reference files, editing and exporting happen here. When you use a cloud model, the text you ask it to work on is sent to that provider under their terms. Local models (such as Ollama) are planned for a later release.",
    keyNote: "API keys are stored in your operating system's keychain and never synced.",
    ollama: "Run models on your own computer. Coming in a later release.",
  },
  home: {
    engineNone: "No AI engine connected. Add an API key to use AI Assist.",
    aiOn: "AI Assist is on",
    aiOff: "AI Assist is off",
  },
  ai: {
    protection: "AI can change content only. Fonts, sizes, spacing and locked layers can't be edited.",
    fitOk: "All proposed text fits your template's limits without overflow.",
    author: "Templix Assist",
  },
  locked: {
    tooltip: "Locked by template",
  },
  fidelity: {
    tooltip: "How closely Templix's reconstruction matches your original file (higher is better).",
  },
} as const;

/** phrases that must never appear in shipped UI copy (NFR-PRIV-04, design.md §9) */
export const FORBIDDEN_PHRASES = [
  "100% on-device",
  "100% privacy",
  "zero cloud",
  "no network calls",
  "ferpa",
  "gdpr compliant",
  "military-grade",
  "pixel-perfect",
  "pixel-matched",
  "local privacy lock",
  "offline sandbox",
] as const;
