import { Route, Routes } from "react-router";
import { ToastProvider } from "@templix/ui";
import { HomePage } from "./screens/Home";
import { HomeLive } from "./screens/HomeLive";
import { AnalysisScreen } from "./screens/Analysis";
import { AnalysisLive } from "./screens/AnalysisLive";
import { ModeScreen } from "./screens/ModePicker";
import { ManualEditorScreen } from "./screens/ManualEditor";
import { ManualLive } from "./screens/ManualLive";
import { DocumentsLive } from "./screens/DocumentsLive";
import { AiAssistScreen } from "./screens/AiAssist";
import { SettingsScreen } from "./screens/Settings";
import { DevUiGallery } from "./dev/ui/Gallery";
import { NotFound } from "./screens/NotFound";
import { ErrorBoundary } from "./lib/ErrorBoundary";

// Fixtures: demo data behind VITE_FIXTURES=1 (e2e/visual work) or ?fixtures=1 at runtime.
// Otherwise Home + Analysis talk to the local server (M2 live mode); later screens stay demo for now.
export const FIXTURE_MODE: boolean =
  import.meta.env.VITE_FIXTURES === "1" || new URLSearchParams(window.location.search).has("fixtures");

export function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Routes>
          <Route path="/" element={FIXTURE_MODE ? <HomePage /> : <HomeLive />} />
          <Route
            path="/templates/:templateId/analysis"
            element={FIXTURE_MODE ? <AnalysisScreen /> : <AnalysisLive />}
          />
          <Route path="/templates/:templateId/mode" element={<ModeScreen />} />
          <Route
            path="/documents/:documentId/manual"
            element={FIXTURE_MODE ? <ManualEditorScreen /> : <ManualLive />}
          />
          <Route path="/documents" element={FIXTURE_MODE ? <NotFound /> : <DocumentsLive />} />
          <Route path="/documents/:documentId/ai" element={<AiAssistScreen />} />
          <Route path="/settings/:section?" element={<SettingsScreen />} />
          <Route path="/dev/ui" element={<DevUiGallery />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ToastProvider>
    </ErrorBoundary>
  );
}
