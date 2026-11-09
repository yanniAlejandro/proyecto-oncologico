# /visual — Comparación visual con la referencia

Captura las pantallas del portal (8 rutas) y del panel (`/admin`, publicaciones, usuarios) + 8 modales para 4 perfiles (visitante, médico sin permisos, editora con permisos, administrador) en escritorio (1440×900) y móvil (390×844), y las compara píxel a píxel con `docs/visual-baseline/` (referencia del portal de cierre, 2026-11-09).

## Requisitos

- API en `localhost:8000` con los seeds cargados (`seed` + `seed_clinical`).
- Frontend levantado (`pnpm dev`). Anota el puerto real: si 4321 está ocupado, Astro usa otro.
- Chromium de Playwright: `pnpm exec playwright install chromium` (o `CHROMIUM_PATH`).

## Pasos

1. `cd frontend && rm -rf ../docs/visual-current && pnpm visual -- --base http://localhost:<puerto>`
2. Lee `docs/visual-current/report.md`.
3. Informa:
   - nº de pantallas y media de diferencia;
   - cada pantalla con **>3 %**, agrupada por causa.
4. Diferencias **esperadas** (no son regresiones):
   - Indicador de la línea de ayuda (cabecera, pie, `07-linea-ayuda`, resumen del panel): depende de la hora de La Habana («Disponible ahora» / «Fuera de horario»).
   - Datos que cambian con el uso: publicaciones, documentos y actividad reciente del panel (`09-panel-resumen`).
   - Rutas sin permiso: el fichero lleva `__redirect_` (visitante → `_login` en guías, protocolos, documentos y `/admin/*`; médico en `/admin/*` y editora en `/admin/usuarios` → portada; `12-login` con sesión → redirige). Si una de estas desaparece o aparece otra, **es un cambio de permisos**: revisarlo.
   - ≤2 % en general: antialiasing.
5. Para cualquier otra diferencia, abre la captura y su `*.diff.png` y explica la causa. No corrijas nada en este comando: propón el arreglo y espera.
