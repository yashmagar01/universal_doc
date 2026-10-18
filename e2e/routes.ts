// Shared route inventory for e2e specs. Fixture ids come from apps/web/src/fixtures/demo.ts
// (VITE_FIXTURES=1). Every M0 screen plus the dev gallery and the 404 route.
//
// Each route names a landmark that must be visible once the screen has mounted. Home/Settings/
// Mode/404/Gallery render AppShell's data-qa="main-content"; the workspace screens
// (analysis/manual/ai) render their own canvas viewport instead.
export interface ScreenRoute {
  name: string;
  path: string;
  /** CSS selector for a landmark that proves the screen mounted */
  landmark: string;
}

export const ROUTES: ScreenRoute[] = [
  { name: "home", path: "/", landmark: '[data-qa="main-content"]' },
  { name: "analysis", path: "/templates/t_newsletter/analysis", landmark: '[data-qa="canvas-viewport"]' },
  { name: "mode", path: "/templates/t_newsletter/mode", landmark: '[data-qa="main-content"]' },
  { name: "manual", path: "/documents/d_march/manual", landmark: '[data-qa="canvas-viewport"]' },
  { name: "ai-assist", path: "/documents/d_march/ai", landmark: '[data-qa="canvas-viewport"]' },
  { name: "settings", path: "/settings", landmark: '[data-qa="main-content"]' },
  { name: "dev-ui", path: "/dev/ui", landmark: '[data-qa="main-content"]' },
  { name: "not-found", path: "/does-not-exist", landmark: '[data-qa="main-content"]' },
];
