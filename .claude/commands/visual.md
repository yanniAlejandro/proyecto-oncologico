# /visual — Comparación visual con el portal original

Captura todas las pantallas (8 rutas + modales) para los 4 roles (visitante, médico, encargado, administrador) en escritorio (1440×900) y móvil (390×844), y las compara píxel a píxel con `docs/visual-baseline/` (capturas del SPA React original, 2026-11-04).

## Requisitos

- API en `localhost:8000` con los seeds cargados (`seed` + `seed_clinical`).
- Frontend levantado (`pnpm dev`). Anota el puerto real: si 4321 está ocupado, Astro usa otro.
- Chromium de Playwright en `~/.cache/ms-playwright` (o `CHROMIUM_PATH`).

## Pasos

1. `cd frontend && rm -rf ../docs/visual-current && pnpm visual -- --base http://localhost:<puerto>`
2. Lee `docs/visual-current/report.md`.
3. Informa:
   - nº de pantallas y media de diferencia;
   - cada pantalla con **>3 %**, agrupada por causa.
4. Diferencias **esperadas** (no son regresiones):
   - `04-documentos`, `m05-documento-nuevo`, `m08-documento-visor`: funcionalidad nueva (subir/ver/descargar).
   - Tablas en móvil (`02-guias`, `03-protocolos`, `07-*`, `08-*`): línea «Desliza la tabla…» (BUG-002) desplaza el contenido ~29 px.
   - ≤2 % en general: antialiasing y fuente autoalojada vs Google Fonts.
5. Para cualquier otra diferencia, abre la captura y su `*.diff.png` y explica la causa. No corrijas nada en este comando: propón el arreglo y espera.
