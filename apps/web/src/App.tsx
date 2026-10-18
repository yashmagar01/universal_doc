import { Route, Routes } from "react-router";
import { ToastProvider } from "@templix/ui";
import { HomePage } from "./screens/Home";
import { AnalysisScreen } from "./screens/Analysis";
import { ModeScreen } from "./screens/ModePicker";
import { ManualEditorScreen } from "./screens/ManualEditor";
import { AiAssistScreen } from "./screens/AiAssist";
import { SettingsScreen } from "./screens/Settings";
import { DevUiGallery } from "./dev/ui/Gallery";
import { NotFound } from "./screens/NotFound";
import { ErrorBoundary } from "./lib/ErrorBoundary";

// Fixtures: demo data is behind VITE_FIXTURES (dev flag). M0 has no backend yet, so data always
// comes from src/fixtures; from M1 on, this flag switches between fixture mode and live API mode.
export const FIXTURE_MODE: boolean = import.meta.env.VITE_FIXTURES === "1";

export function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/templates/:templateId/analysis" element={<AnalysisScreen />} />
          <Route path="/templates/:templateId/mode" element={<ModeScreen />} />
          <Route path="/documents/:documentId/manual" element={<ManualEditorScreen />} />
          <Route path="/documents/:documentId/ai" element={<AiAssistScreen />} />
          <Route path="/settings/:section?" element={<SettingsScreen />} />
          <Route path="/dev/ui" element={<DevUiGallery />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ToastProvider>
    </ErrorBoundary>
  );
}
