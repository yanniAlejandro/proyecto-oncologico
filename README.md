# Portal Oncológico — Hospital Oncológico de La Habana

Monorepo con dos partes independientes:

| Carpeta | Stack | Gestor |
|---|---|---|
| `frontend/` | Astro 7 (SSR) + islas React 19 + Tailwind 4 + shadcn/ui | pnpm |
| `backend/` | FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + Alembic | conda (`oncologico`) |
| `database/` | Scripts SQL heredados (solo referencia; el esquema lo gestiona Alembic) | — |

## Vistas y roles

| Vista | Ruta | Acceso |
|---|---|---|
| Noticias (inicio) | `/` | Público. Login desde aquí |
| Guías de diagnóstico | `/guias-diagnostico` | Médico, encargado, admin |
| Protocolos de tratamiento | `/protocolos-tratamiento` | Público (lectura) |
| Documentos | `/documentos` | Público: ver y descargar. Encargado/admin: subir y eliminar |
| Enlaces de interés | `/enlaces` | Público |
| Contacto | `/contacto` | Público |
| Gestión de noticias | `/gestion/noticias` | Encargado, admin |
| Gestión de usuarios | `/gestion/usuarios` | Admin (alta/baja de médicos) |

Las guardas de ruta se aplican en el servidor (middleware de Astro) y cada endpoint de la API vuelve a comprobar el rol.

## Arquitectura

```
Navegador ──► Astro (Node, SSR) ──────────────► FastAPI ──► PostgreSQL
              · páginas .astro + islas React       · /api/v1        └─► STORAGE_DIR (archivos)
              · /api/auth/login|logout (cookie)
              · /api/v1/* → proxy a FastAPI con el token
```

- El navegador **solo habla con Astro**. El JWT vive en una cookie `httpOnly` (`holh_session`) que el JavaScript no puede leer; el proxy `/api/v1/*` de Astro añade `Authorization: Bearer …` antes de llamar a FastAPI. No hace falta CORS.
- Las páginas se renderizan en el servidor con los datos ya cargados; las partes interactivas (tablas con búsqueda, formularios, visor) son **islas React**. La navegación entre pestañas no recarga el documento (`<ClientRouter />`).
- **Roles en dos capas**: el middleware de Astro decide qué páginas se pueden abrir y qué botones se muestran; FastAPI es la autoridad y comprueba el rol en cada caso de uso (401 sin sesión, 403 sin permiso).

### Backend — slices verticales por funcionalidad

```
backend/app/
├── main.py                       # composición: crea la app e incluye el router de cada feature
├── shared/
│   ├── domain/                   # Result (Ok/Err + AppError) · Actor, Role y reglas de permisos
│   ├── infrastructure/           # config, BD (SQLAlchemy async), bcrypt, JWT, registro ORM
│   └── presentation/errors.py    # AppError → código HTTP
└── features/                     # users · auth · news · diseases · clinical_content · documents · interest_links · contact
    └── <feature>/
        ├── domain/               # modelos y reglas puras + puertos (interfaces). Sin FastAPI ni SQLAlchemy
        ├── application/          # casos de uso: comprueban el rol y devuelven Result
        ├── infrastructure/       # adaptadores: ORM + repositorio SQL, almacenamiento en disco…
        └── presentation/         # router FastAPI, schemas Pydantic e inyección de dependencias (Depends)
```

- **Inyección de dependencias** con `Depends()`: cada router recibe sus repositorios/servicios por proveedores, que los tests sustituyen con `app.dependency_overrides`.
- **Esquema**: modelos ORM + migraciones Alembic (`backend/alembic/versions/`). No se escribe SQL a mano.
- **Tests**: casos de uso con *fakes* en memoria (sin mocks), capa HTTP con `TestClient` y repositorios contra PostgreSQL real.

### Frontend — Astro + islas React + shadcn/ui

```
frontend/src/
├── middleware.ts                 # cookie → usuario (GET /auth/me) · guardas de rol por ruta
├── layouts/BaseLayout.astro      # barra institucional, cabecera, menú según rol, pie
├── pages/                        # una ruta por fichero + api/auth/* (sesión) + api/v1/[...path] (proxy)
├── features/<feature>/
│   ├── domain/                   # tipos y reglas puras (p. ej. qué se puede previsualizar)
│   ├── infrastructure/           # create<X>Api(transport): la misma API en el servidor y en las islas
│   └── presentation/             # islas React (reciben los datos iniciales del SSR)
├── components/ui/                # shadcn/ui (Radix) con los estilos del hospital
├── components/site/              # cabecera de página, buscador, tabla, diálogos
├── shared/                       # transporte HTTP, roles y sesión, TanStack Query
└── styles/global.css             # colores HOLH (Tailwind 4 @theme) + maquetación del portal
```

### Documentos: subida, visor y descarga

1. Encargado/admin sube desde el diálogo (arrastrar o seleccionar). El navegador valida formato y tamaño, y FastAPI **vuelve a validar**: rol, nombre saneado, lista blanca de formatos, que el contenido corresponda a la extensión y tamaño máximo (`MAX_UPLOAD_MB`, 25 MB).
2. El archivo se guarda en `STORAGE_DIR/<2 primeros>/<uuid>.<ext>` (escritura atómica, permisos 600). En la BD quedan título, nombre original, tipo, tamaño y la clave de almacenamiento. Si falla la BD, el archivo se borra.
3. Cualquiera ve (`?disposition=inline`, solo PDF, imágenes y TXT) o descarga (`attachment`) desde `GET /documents/{id}/file`. Al eliminar se borran la fila y el archivo.

El almacenamiento está detrás de una interfaz (`FileStorage`): hoy es disco local, y se puede cambiar por NFS o MinIO/S3 sin tocar la lógica.

## Puesta en marcha

### 1. Backend (entorno conda aislado: Python 3.12 + PostgreSQL 16)

```bash
conda create -n oncologico -c conda-forge python=3.12 postgresql=16
conda activate oncologico

cd backend
pip install -r requirements-dev.txt
cp .env.example .env                       # ajusta SECRET_KEY

# PostgreSQL local dentro del entorno (datos en backend/.pgdata, ignorado por git)
initdb -D .pgdata -U postgres -W -A scram-sha-256 -E UTF8 --locale=C.UTF-8   # contraseña: postgres
pg_ctl -D .pgdata -l .pgdata/server.log -o "-p 5432 -k /tmp" start
psql -h localhost -U postgres -c "CREATE DATABASE oncologico;"

alembic upgrade head                       # crea el esquema
python -m app.scripts.seed                 # usuarios, contacto, enfermedades, enlaces, noticia
python -m app.scripts.seed_clinical        # guías, protocolos y documentos (con PDF/DOCX de ejemplo)

uvicorn app.main:app --reload --port 8000  # docs: http://localhost:8000/docs
```

> BD creada con el antiguo `database/schema.sql`: `alembic stamp 0001 && alembic upgrade head`.

### 2. Frontend

```bash
cd frontend
pnpm install
cp .env.example .env      # API_URL=http://localhost:8000/api/v1
pnpm dev                  # http://localhost:4321
```

## Tests y calidad

```bash
# backend (conda activate oncologico; cd backend)
pytest                                     # casos de uso con fakes + capa HTTP (sin BD)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/oncologico_test pytest  # + integración SQL (85 en total)
ruff check . && ruff format --check .

# frontend (cd frontend)
pnpm test && pnpm typecheck && pnpm build   # 25 tests Vitest
pnpm exec playwright install chromium      # una vez, para los E2E
pnpm visual -- --base http://localhost:4321   # regresión visual contra docs/visual-baseline (local)
E2E_BASE_URL=http://localhost:4321 pnpm e2e   # E2E: subir/ver/descargar/eliminar documento (E2E_KEEP=1 conserva el archivo)
```

## Despliegue (red del hospital)

```bash
# backend: variables en backend/.env
SECRET_KEY=<aleatoria>          # python3 -c "import secrets; print(secrets.token_urlsafe(48))"
DATABASE_URL=postgresql+asyncpg://usuario:clave@host:5432/oncologico
STORAGE_DIR=/srv/holh/documentos   # absoluta; si es relativa se resuelve dentro de backend/
MAX_UPLOAD_MB=25
alembic upgrade head && uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2

# frontend: variables en frontend/.env
API_URL=http://127.0.0.1:8000/api/v1
SESSION_COOKIE_SECURE=true      # si se sirve por HTTPS
pnpm build && HOST=0.0.0.0 PORT=4321 node --env-file=.env dist/server/entry.mjs   # en producción .env no se carga solo
```

- Los archivos subidos quedan en la máquina donde corre **FastAPI**, en `STORAGE_DIR`. **Haz copia de seguridad de esa carpeta junto con la BD.**
- Con Docker, monta `STORAGE_DIR` como volumen. Con varias instancias de la API en distintas máquinas, usa almacenamiento compartido (NFS o MinIO).
- Si hay un proxy delante (nginx…), sube su límite de petición: `client_max_body_size 25m;`.
- Solo Astro necesita ser accesible desde la red; FastAPI puede escuchar en `127.0.0.1`.

## Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@oncologico.com | Admin123! |
| Encargado | encargado@oncologico.com | Encargado123! |
| Médico | medico@oncologico.com | Medico123! |

## API (`/api/v1`)

- `POST /auth/login` · `GET /auth/me`
- `GET/POST/PUT/DELETE /news` (+ `GET /news/manage`)
- `GET/POST/PUT/DELETE /diagnostic-guides` · `/treatment-protocols` · `GET/POST /diseases`
- `GET /documents` · `POST /documents` (multipart: `file` o `file_url`) · `GET|HEAD /documents/{id}/file?disposition=inline|attachment` · `DELETE /documents/{id}` · `GET /documents/upload-policy`
- `GET/POST/PUT/DELETE /interest-links` · `GET/PUT /contact` · `GET/POST/DELETE /users`

Documentación interactiva: http://localhost:8000/docs · Convenciones de código: [`.claude/CLAUDE.md`](.claude/CLAUDE.md).
