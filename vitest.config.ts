import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom",
    include: ["{apps,packages}/**/tests/**/*.test.{ts,tsx}"],
    exclude: ["**/node_modules/**", "**/.git/**"],
  },
});
