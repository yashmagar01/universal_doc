import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// NFR-A11Y-01 (WCAG AA): core text tokens must meet 4.5:1 on the surfaces they are drawn on.
// Parses the real theme.css so the test tracks the design tokens, not a copy of them.

const themeCss = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../src/theme.css"), "utf8");

const tokens: Record<string, string> = {};
for (const m of themeCss.matchAll(/--color-([a-z0-9-]+):\s*(#[0-9a-f]{6});/gi)) {
  tokens[m[1]!] = m[2]!;
}

function lin(channel: number): number {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrast(a: string, b: string): number {
  const la = luminance(a);
  const lb = luminance(b);
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

// (foreground, background, minimum) pairs actually used in the UI.
const PAIRS: [string, string][] = [
  ["ink", "card"],
  ["ink", "canvas"],
  ["ink-2", "card"],
  ["ink-2", "canvas"],
  ["brand", "card"],
  ["on-primary", "brand"], // primary button: white on brand
  ["on-primary", "error"],
  ["on-primary", "warning"],
  ["error", "card"],
  ["success", "card"],
  ["warning", "card"],
];

describe("theme token contrast (WCAG AA 4.5:1)", () => {
  it("parsed the expected core tokens", () => {
    for (const name of ["ink", "ink-2", "brand", "card", "canvas"]) {
      expect(tokens[name], `--color-${name} missing from theme.css`).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });

  for (const [fg, bg] of PAIRS) {
    it(`${fg} on ${bg} >= 4.5:1`, () => {
      expect(tokens[fg], `--color-${fg} missing`).toBeTruthy();
      expect(tokens[bg], `--color-${bg} missing`).toBeTruthy();
      expect(contrast(tokens[fg]!, tokens[bg]!)).toBeGreaterThanOrEqual(4.5);
    });
  }
});
