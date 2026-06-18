import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    emptyOutDir: true,
    outDir: "../dist",
  },
  test: {
    environment: "node",
    globals: true,
  },
});
