import { defineConfig, devices } from "@playwright/test";

/**
 * E2E contra la app real (API en :8000 con seeds + `pnpm dev`).
 *   E2E_BASE_URL   URL del frontend (por defecto http://localhost:4321)
 *   E2E_SLOWMO     ms entre acciones, para verlo en modo --headed (por defecto 0)
 *   E2E_KEEP=1     no borra el documento subido al final (para inspeccionar el archivo)
 * Resultados (vídeo, trazas, informe) en ../docs/e2e/ (memoria local, ignorada por git).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  outputDir: "../docs/e2e/results",
  reporter: [["list"], ["html", { outputFolder: "../docs/e2e/report", open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:4321",
    locale: "es-ES",
    video: "on",
    trace: "on",
    launchOptions: { slowMo: Number(process.env.E2E_SLOWMO ?? 0) },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
