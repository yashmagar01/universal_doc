// Landmark regions per screen for NFR-TEST-04 parity.
//
// design.md §14 compares our landmark geometry against the Stitch design at 1333x900 @ DPR 1.2,
// within +/-4% on position and size. The Stitch exports carry no data-qa, so this file lists OUR
// named regions (by data-qa) that a stitch<->ours mapping would compare.
//
// Status: scaffold only. parity.spec.ts captures our region geometry + a screenshot per screen into
// artifacts/parity/ for human review. The numeric stitch comparison (and any +/-4% gate) is deferred
// until the mapping is visually signed off against the Stitch PNGs.

export interface Region {
  /** Human name used in the artifacts and in a future stitch mapping */
  name: string;
  /** Our data-qa selector */
  selector: string;
  /** Which screen this region belongs to (must match ROUTES[].name) */
  screen: string;
}

// The six design screens (design.md §14). Only data-qa values that actually exist in the app.
export const REGIONS: Region[] = [
  // App shell — present on every screen
  { screen: "home", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "home", name: "nav-tabs", selector: '[data-qa="nav-tabs"]' },
  { screen: "home", name: "profile-chip", selector: '[data-qa="profile-chip"]' },
  { screen: "home", name: "main-content", selector: '[data-qa="main-content"]' },
  { screen: "home", name: "template-card", selector: '[data-qa="template-card"]' },

  { screen: "mode", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "mode", name: "nav-tabs", selector: '[data-qa="nav-tabs"]' },
  { screen: "mode", name: "main-content", selector: '[data-qa="main-content"]' },

  { screen: "analysis", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "analysis", name: "workspace-top-bar", selector: '[data-qa="workspace-top-bar"]' },
  { screen: "analysis", name: "sidebar-left", selector: '[data-qa="sidebar-left"]' },
  { screen: "analysis", name: "canvas-viewport", selector: '[data-qa="canvas-viewport"]' },
  { screen: "analysis", name: "canvas", selector: '[data-qa="canvas"]' },
  { screen: "analysis", name: "sidebar-right", selector: '[data-qa="sidebar-right"]' },

  { screen: "manual", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "manual", name: "workspace-top-bar", selector: '[data-qa="workspace-top-bar"]' },
  { screen: "manual", name: "sidebar-left", selector: '[data-qa="sidebar-left"]' },
  { screen: "manual", name: "canvas-viewport", selector: '[data-qa="canvas-viewport"]' },
  { screen: "manual", name: "floating-toolbar", selector: '[data-qa="floating-toolbar"]' },
  { screen: "manual", name: "status-bar", selector: '[data-qa="status-bar"]' },
  { screen: "manual", name: "sidebar-right", selector: '[data-qa="sidebar-right"]' },

  { screen: "ai-assist", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "ai-assist", name: "workspace-top-bar", selector: '[data-qa="workspace-top-bar"]' },
  { screen: "ai-assist", name: "canvas-viewport", selector: '[data-qa="canvas-viewport"]' },
  { screen: "ai-assist", name: "status-bar", selector: '[data-qa="status-bar"]' },
  { screen: "ai-assist", name: "quick-replies", selector: '[data-qa="quick-replies"]' },

  { screen: "settings", name: "top-bar", selector: '[data-qa="top-bar"]' },
  { screen: "settings", name: "nav-tabs", selector: '[data-qa="nav-tabs"]' },
  { screen: "settings", name: "main-content", selector: '[data-qa="main-content"]' },
  { screen: "settings", name: "settings-nav", selector: '[data-qa="settings-nav"]' },
];

export const PARITY_SCREENS = ["home", "mode", "analysis", "manual", "ai-assist", "settings"] as const;

export function regionsFor(screen: string): Region[] {
  return REGIONS.filter((r) => r.screen === screen);
}
