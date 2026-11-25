import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// jsdom no trae ResizeObserver, que usan las gráficas.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

afterEach(() => {
  cleanup();
  localStorage.clear();
  window.location.hash = "";
  vi.unstubAllGlobals();
});
