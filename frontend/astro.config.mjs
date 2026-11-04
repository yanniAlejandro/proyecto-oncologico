// @ts-check
import node from "@astrojs/node";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, envField } from "astro/config";

export default defineConfig({
  // SSR: sesión en cookie httpOnly + guardas de rol en el middleware.
  output: "server",
  adapter: node({ mode: "standalone" }),
  integrations: [react()],
  server: { port: 4321 },
  // Toolbar de desarrollo (Inspect, auditoría a11y…). `pnpm visual` la oculta en las capturas.
  devToolbar: { enabled: true },
  // Con <ClientRouter /> los enlaces se precargan al pasar el ratón.
  prefetch: { prefetchAll: true, defaultStrategy: "hover" },
  trailingSlash: "never",
  security: { checkOrigin: true },
  env: {
    schema: {
      API_URL: envField.string({
        context: "server",
        access: "public",
        default: "http://localhost:8000/api/v1",
      }),
      SESSION_COOKIE_SECURE: envField.boolean({ context: "server", access: "public", default: false }),
    },
  },
  vite: { plugins: [tailwindcss()] },
});
