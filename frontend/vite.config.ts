import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // En GitHub Pages la app vive en /<repositorio>/; el flujo de despliegue define VITE_BASE.
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/pruebas/preparar.ts",
    css: false,
  },
});
