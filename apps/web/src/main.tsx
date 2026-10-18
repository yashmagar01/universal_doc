import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import "./index.css";
import { App } from "./App";
import { TooltipProvider } from "@templix/ui";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <TooltipProvider delayDuration={300}>
        <App />
      </TooltipProvider>
    </BrowserRouter>
  </StrictMode>,
);
