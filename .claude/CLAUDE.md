# Portal Oncológico — Hospital Oncológico de La Habana (tesis)

Portal institucional del Hospital Oncológico de La Habana: «Quiénes somos» (portada), publicaciones con vista previa de enlaces, guías de diagnóstico, protocolos de tratamiento, repositorio de documentos (subir / ver / descargar), enlaces, línea de ayuda y contacto. Portal público de solo consulta + panel de gestión `/admin` con permisos por sección. Monorepo con dos partes independientes.

---

## Tech Stack

| Parte | Stack |
|---|---|
| **frontend/** | Astro 7 (SSR, adaptador Node) + islas React 19, Tailwind CSS 4, shadcn/ui (Radix + CVA), TanStack Query, Vitest + Testing Library. **pnpm**. |
| **backend/** | FastAPI + SQLAlchemy 2 (async, asyncpg) + PostgreSQL 16, Alembic, Pydantic 2, pytest. Entorno **conda** `oncologico` (Python 3.12 + PostgreSQL). |

## Commands

```bash
# Backend (siempre dentro del entorno conda)
conda activate oncologico
pg_ctl -D backend/.pgdata -l backend/.pgdata/server.log -o "-p 5432 -k /tmp" start   # BD local
cd backend
pip install -r requirements-dev.txt
alembic upgrade head                      # esquema (fuente de verdad: modelos ORM + alembic/versions)
python -m app.scripts.seed && python -m app.scripts.seed_clinical
uvicorn app.main:app --reload --port 8000 # http://localhost:8000/docs
pytest                                    # unitarios + HTTP (sin BD)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/oncologico_test pytest   # + integración
ruff check . && ruff format --check .

# Frontend
cd frontend
pnpm install
pnpm dev            # http://localhost:4321 (si está ocupado, Astro usa el siguiente libre)
pnpm test           # vitest
pnpm typecheck      # astro check
pnpm build && pnpm preview
pnpm visual -- --base http://localhost:4321   # capturas + comparación con docs/visual-baseline
E2E_BASE_URL=http://localhost:4321 pnpm e2e   # Playwright E2E (resultados en docs/e2e/); pnpm e2e:headed para verlo
```

---

## Arquitectura

### Backend — slices verticales + DI (`backend/app/`)

```
app/
├── main.py                     # composition root: create_app() incluye los routers de cada feature
├── shared/
│   ├── domain/                 # Result (Ok/Err + AppError), Actor + Role + Section (permisos), FileStorage, image_policy
│   ├── infrastructure/         # config, database (Base, get_session), security (bcrypt, JWT), local_storage, orm_registry
│   └── presentation/errors.py  # AppError → HTTP (unwrap)
└── features/<feature>/         # users, auth, publications, about, helpline, diseases, clinical_content, documents, interest_links, contact
    ├── domain/                 # dataclasses + reglas puras + puertos (Protocol). Sin FastAPI/SQLAlchemy.
    ├── application/use_cases.py# una clase por caso de uso (__call__), recibe Actor, devuelve Result
    ├── infrastructure/         # orm.py (SQLAlchemy), repository.py (adaptador), otros adaptadores (local_storage)
    └── presentation/           # router.py + schemas Pydantic + providers Depends() (la DI); deps.py si otra feature los usa
```

Reglas:
- `domain` no importa frameworks. `presentation` solo llama casos de uso, nunca repositorios para lógica.
- **Los permisos se comprueban en el caso de uso**, no en el router: `require_section(actor, Section.X)` para gestionar, `require_admin` (usuarios, contacto), `require_user` (leer guías y protocolos). Así se testean sin HTTP.
- Nueva sección gestionable → añadir a `Section` (backend) y a `SECTIONS`/`SECTION_LABELS`/`ADMIN_NAV` (frontend, `shared/auth/roles.ts`). `user_permissions.section` es texto: no requiere migración.
- Descargas de URLs de usuarios (vista previa de publicaciones): siempre por `HttpLinkPreviewer` (protección SSRF). Nunca `httpx.get(url)` directo.
- Fallos esperados → `Err(AppError.xxx(...))`; excepciones solo para bugs. El router hace `unwrap(...)`.
- Entre features solo se importa `domain`/`application` (excepción: `auth.presentation.deps.CurrentActor` y providers `deps.py`).
- Tras `commit()`, no leer atributos de una fila después de `expire_all()` (dispara IO síncrono → `MissingGreenlet`).
- Esquema: cambiar el modelo ORM y crear migración (`alembic revision --autogenerate -m "..."`), revisarla y `alembic check`.

### Frontend — Astro SSR + islas (`frontend/src/`)

```
src/
├── middleware.ts           # cookie → /auth/me → locals.user (con permisos); guardas del panel (ADMIN_NAV) y redirección /gestion/* → /admin/*
├── layouts/                # BaseLayout (portal) · AdminLayout (panel /admin, barra lateral) · HeadCommon
├── pages/                  # portal (solo lectura) + admin/* (panel) + api/auth/{login,logout}.ts + api/v1/[...path].ts (proxy)
├── features/<feature>/
│   ├── domain/             # tipos + reglas puras (p. ej. documents: previewKind, validateFile)
│   ├── infrastructure/     # create<X>Api(transport) — misma API en SSR y en islas
│   └── presentation/       # islas React (reciben initialItems del SSR y `api` inyectable para tests)
├── components/ui/          # shadcn (button, dialog, alert-dialog, input, ...) con estilos HOLH
├── components/site/        # PageHeader, SearchBar, DataTable, FormDialog, ContentDialog, HospitalLogo
├── shared/                 # api/transport (puerto) + server/browser (adaptadores), auth/roles+session, query, hooks
└── styles/global.css       # tokens --holh-* → @theme Tailwind + maquetación del portal (@layer components)
```

Reglas:
- **Sesión**: el JWT vive en cookie httpOnly `holh_session`; el navegador nunca lo ve. Las islas llaman a `/api/v1/*` (proxy de Astro), que añade `Authorization`.
- Permisos de UI con `shared/auth/roles.ts` (espejo de `app/shared/domain/actor.py`): `can(user, section)`, `isAdmin`, `canUsePanel`. El backend es la autoridad: la UI solo oculta.
- Las páginas públicas **no** gestionan nada. Toda la gestión vive en `/admin/*`; cada pantalla del panel se declara en `ADMIN_NAV` (ruta, grupo, icono y requisito), que alimenta la barra lateral y las guardas del middleware.
- Textos editables con formato: `components/site/RichText.tsx` (sin HTML). Nunca `set:html` con contenido de usuarios.
- `.astro` para lo estático; `.tsx` solo para islas interactivas (`client:load`).
- `tailwind-merge`: el interlineado va en la misma clase que el tamaño (`text-[0.9rem]/[normal]`), si no se descarta.

## Roles

| Rol | Puede |
|---|---|
| Visitante | Portal público: quiénes somos, publicaciones, documentos (ver/descargar), enlaces, línea de ayuda, contacto |
| Médico | + guías y protocolos (lectura). Por defecto solo lee; gestiona (CRUD completo) las secciones que le conceda un admin |
| Administrador | Todo + contacto + usuarios y permisos (también otros admins). Salvaguardas: no auto-desactivarse/degradarse, nunca 0 admins |

## Design Constraints

- **Referencia visual**: `docs/visual-baseline/` (portal de cierre, 2026-11-09). La del SPA React original se conserva en `docs/visual-baseline-original/`. Verificar con `/visual`.
- Colores HOLH (`--holh-blue #0b3d5c`, `--holh-teal #2a8f9e`, …) y fuente Source Sans 3 (autoalojada): no cambiar.
- Español en UI, mensajes de error y commits de documentación.

---

## Project Memory (`docs/`)

`docs/` está **ignorado por git**: es la memoria local del proyecto (sobrevive entre sesiones, no viaja con el repo).

| Ruta | Para qué |
|---|---|
| `docs/tasks/todo/` | Backlog. Un `.md` por tarea con frontmatter (`date`, `priority`). |
| `docs/tasks/in-progress/` | Trabajo activo (máx. 1-2). |
| `docs/SESSION-LOG.md` | Registro de sesiones, la más reciente arriba. Lo actualiza `/done`. |
| `docs/BUGS.md` | Bugs con estado `open`/`fixed` y fichero de referencia. |
| `docs/decisions/` | ADRs (`YYYY-MM-DD-slug.md`). |
| `docs/visual-baseline/` | Referencia visual actual (portal + panel, 4 perfiles). **No regenerar** salvo cambio de diseño acordado. |
| `docs/visual-baseline-original/` | Capturas del SPA React original (histórico, no se compara). |
| `docs/visual-current/` | Última captura de `/visual` + `report.md` + `*.diff.png`. |
| `docs/*.md` | Documentos de tema (análisis, guías). |

### Task board
- "trabaja en X" → mover el fichero de `todo/` a `in-progress/`.
- `/done` borra las tareas terminadas de `in-progress/` (no hay `done/`; el registro queda en SESSION-LOG y git) y actualiza las parciales.
- Crear tareas nuevas en `todo/` cuando aparezcan durante el trabajo.

### Comportamientos automáticos
- **Bugs**: antes de registrar uno, mirar `docs/BUGS.md`. Nuevo → `## Open` con ID incremental, severidad, **fichero**, descripción y fecha. Al arreglarlo → `## Fixed` con fecha y commit. Los bugs pueden quedar obsoletos: verificar el fichero antes de darlo por abierto.
- **Decisiones**: elecciones técnicas no triviales → `docs/decisions/YYYY-MM-DD-slug.md` (frontmatter `date`, `tags`, `status: accepted`; Contexto, Opciones, Decisión, Consecuencias, Ficheros; 20-40 líneas). No para decisiones rutinarias.

### Comandos de sesión

| Comando | Cuándo | Qué hace |
|---|---|---|
| `/brief` | Inicio de sesión | Lee log, tareas, bugs, git → resumen de 15 s |
| `/visual` | Tras cambios de UI | Captura todas las pantallas por rol y compara con la referencia |
| `/done` | Fin de sesión | Actualiza log/bugs/tareas, ejecuta tests y build, propone commit |
