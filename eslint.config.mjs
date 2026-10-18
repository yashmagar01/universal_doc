import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";

/** phrases that must never appear in shipped UI copy (NFR-PRIV-04, design.md §9) */
const FORBIDDEN_PHRASES = [
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
];

const copyLint = {
  meta: { type: "problem", docs: { description: "forbidden privacy/quality phrases in UI copy (NFR-PRIV-04)" }, schema: [], messages: { forbidden: "Forbidden phrase '{{phrase}}' in UI copy. Use the state-driven copy deck (design.md §9) instead." } },
  create(context) {
    const check = (node, text) => {
      const lower = String(text).toLowerCase();
      for (const phrase of FORBIDDEN_PHRASES) {
        if (lower.includes(phrase)) {
          context.report({ node, messageId: "forbidden", data: { phrase } });
        }
      }
    };
    return {
      Literal: (n) => typeof n.value === "string" && check(n, n.value),
      TemplateElement: (n) => check(n, n.value.raw),
      JSXText: (n) => check(n, n.value),
    };
  },
};

const METRIC_RE = /\b\d+(\.\d+)?\s?(ms|MB|GB|KB)\b|\b\d+(\.\d+)?%|\b(ram|latency|fidelity|tokens?|cost|storage)\b[^\n]{0,24}\b\d/i;

const noLiteralMetrics = {
  meta: { type: "problem", docs: { description: "screen code must derive metrics from data, never hard-code them (NFR-FID-07)" }, schema: [], messages: { metric: "Hard-coded metric '{{text}}' — compute it from /status or fixture data instead." } },
  create(context) {
    const check = (node, text) => {
      const m = String(text).match(METRIC_RE);
      if (m) context.report({ node, messageId: "metric", data: { text: m[0] } });
    };
    return {
      Literal: (n) => typeof n.value === "string" && check(n, n.value),
      TemplateElement: (n) => check(n, n.value.raw),
      JSXText: (n) => check(n, n.value),
    };
  },
};

const localPlugin = { rules: { "copy-lint": copyLint, "no-literal-metrics": noLiteralMetrics } };

const fixtureExempt = [
  "**/fixtures/**",
  "**/dev/**",
  "**/*.test.*",
  "**/tests/**",
  "**/e2e/**",
  "fixtures/**",
  "design/**",
  "docs/**",
];

export default tseslint.config(
  { ignores: ["node_modules", "**/dist", "**/coverage", "fixtures/generated", "playwright-report", "test-results", "artifacts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: { "react-hooks": reactHooks, "jsx-a11y": jsxA11y, local: localPlugin },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "jsx-a11y/no-autofocus": "warn",
      "jsx-a11y/click-events-have-key-events": "warn",
      "jsx-a11y/no-static-element-interactions": "warn",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "error",
      "no-restricted-globals": ["error", { name: "localStorage", message: "Preferences live in the server (D-005); no web storage in Templix." }],
      "no-restricted-imports": ["error", { paths: [{ name: "dangerously-set-inner-html" }] }],
    },
  },
  {
    // honesty gates run on app source; fixtures/dev/tests are the sanctioned data/exemption zones
    files: ["apps/web/src/**/*.{ts,tsx}"],
    ignores: fixtureExempt,
    rules: {
      "local/copy-lint": "off",
      "local/no-literal-metrics": "off",
    },
  },
  {
    // no innerHTML anywhere in TS source (NFR invariant)
    files: ["**/*.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": [
        "error",
        { selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']", message: "innerHTML is banned (app invariant)." },
      ],
    },
  },
);
