import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { svelteTesting } from "@testing-library/svelte/vite";

export default defineConfig({
  // svelteTesting only affects vitest runs: it forces browser-side
  // Svelte resolution so render() doesn't pick the server entry
  // ("mount(...) is not available on the server" under Vite >= 6).
  plugins: [svelte(), svelteTesting()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    // Proxy /api → backend so the browser sees same-origin requests and
    // the frontend API client stays free of an explicit base URL.
    // VITE_PROXY_TARGET defaults to the docker-compose hostname; CI
    // overrides to localhost where backend is on the same host.
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET ?? "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    // Playwright e2e specs live alongside the vitest unit tests but
    // are driven separately by `playwright test`.
    exclude: ["tests/e2e/**", "node_modules/**"],
  },
});
