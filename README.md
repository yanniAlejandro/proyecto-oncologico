# Portal Oncológico — Hospital Oncológico de La Habana

Monorepo con dos partes independientes:

| Carpeta | Stack | Gestor |
|---|---|---|
| `frontend/` | Astro 7 (SSR) + islas React 19 + Tailwind 4 + shadcn/ui | pnpm |
| `backend/` | FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + Alembic | conda (`oncologico`) |
| `database/` | Scripts SQL heredados (solo referencia; el esquema lo gestiona Alembic) | — |

## Vistas, roles y permisos

**Portal público** (solo consulta: no hay botones de gestión):

| Vista | Ruta | Acceso |
|---|---|---|
| Quiénes somos (portada) | `/` | Público. Login desde aquí |
| Publicaciones | `/publicaciones` | Público |
| Guías de diagnóstico | `/guias-diagnostico` | Con sesión (médico o admin) |
| Protocolos de tratamiento | `/protocolos-tratamiento` | Con sesión (médico o admin) |
| Documentos | `/documentos` | Público: ver y descargar |
| Enlaces de interés | `/enlaces` | Público |
| Línea de ayuda | `/linea-de-ayuda` | Público (y en la cabecera y el pie de todas las páginas) |
| Contacto | `/contacto` | Público |

**Panel de gestión** (`/admin`, layout propio con barra lateral): resumen + una pantalla por sección.

| Rol | Puede |
|---|---|
| Visitante | Ver el portal público |
| Médico | Por defecto, **solo ver y descargar** (incluidas guías y protocolos). Gestiona (CRUD completo, también lo de otros) **solo las secciones que un administrador le conceda**: publicaciones, guías, protocolos, enfermedades, documentos, enlaces, quiénes somos, línea de ayuda |
| Administrador | Todo, incluidos contacto y **usuarios y permisos** (crear médicos y administradores, conceder permisos, desactivar/reactivar, cambiar contraseñas) |

Salvaguardas: nadie se desactiva ni se quita el rol de administrador a sí mismo, y siempre queda al menos un administrador activo. Los permisos se leen de la BD en cada petición: conceder o retirar uno tiene efecto inmediato. Las guardas se aplican en el servidor (middleware de Astro) y cada endpoint de la API vuelve a comprobar el permiso.

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
│   ├── domain/                   # Result · Actor, Role, Section y require_section · FileStorage · política de imágenes
│   ├── infrastructure/           # config, BD (SQLAlchemy async), bcrypt, JWT, registro ORM
│   └── presentation/errors.py    # AppError → código HTTP
└── features/                     # users · auth · publications · about · helpline · diseases · clinical_content · documents · interest_links · contact
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
├── layouts/                      # BaseLayout (portal: barra con la línea de ayuda, menú, pie) · AdminLayout (panel con barra lateral)
├── pages/                        # portal + admin/* (panel) + api/auth/* (sesión) + api/v1/[...path] (proxy)
├── features/<feature>/
│   ├── domain/                   # tipos y reglas puras (p. ej. qué se puede previsualizar)
│   ├── infrastructure/           # create<X>Api(transport): la misma API en el servidor y en las islas
│   └── presentation/             # islas React (reciben los datos iniciales del SSR)
├── components/ui/                # shadcn/ui (Radix) con los estilos del hospital
├── components/site/              # cabecera de página, buscador, tabla, diálogos
├── shared/                       # transporte HTTP, roles/permisos/menú del panel (auth/roles.ts), sesión, TanStack Query
└── styles/global.css             # colores HOLH (Tailwind 4 @theme) + maquetación del portal
```

### Publicaciones: vista previa del enlace (como WhatsApp)

1. Al pegar la URL, `POST /publications/preview` lee las etiquetas Open Graph de la página (`og:title`, `og:description`, `og:image`) y autocompleta el formulario sin pisar lo que ya escribió el usuario.
2. Al guardar, la imagen **se descarga y se guarda** en `STORAGE_DIR` (no se enlaza la original). Si no hay vista previa o la imagen no se puede descargar, se completa a mano (título y, opcionalmente, una imagen subida).
3. **Protección SSRF**: el servidor solo descarga `http/https` por los puertos 80/443 y solo si **todas** las IP del host son públicas (también en cada redirección, máx. 3); timeout 5 s, máx. 2 MB de HTML y 5 MB de imagen; la imagen se valida por su contenido (PNG/JPEG/GIF/WebP). Necesita salida a Internet desde la máquina de FastAPI; sin ella, todo funciona en modo manual.

### Línea de ayuda

Teléfono del hospital y lista independiente de profesionales, cada uno con franjas semanales. El indicador «Disponible ahora / Fuera de horario» se calcula con la hora de La Habana; fuera de horario se muestra el mensaje y el número de urgencias. El panel avisa si algún día no cubre las **6 horas** del estándar. La cabecera se cachea 30 s en el servidor de Astro.

### Quiénes somos

Portada en apartados ordenados (título, texto con formato básico —párrafos, listas `- `, subtítulos `### `, `**negrita**`, notas `> `— y foto opcional). El texto nunca se interpreta como HTML. Se cargan seis **borradores pendientes de validar** (datos a completar entre `[corchetes]`).

### Documentos: subida, visor y descarga

1. Quien tenga el permiso «documentos» sube desde el panel (`/admin/documentos`) (arrastrar o seleccionar). El navegador valida formato y tamaño, y FastAPI **vuelve a validar**: rol, nombre saneado, lista blanca de formatos, que el contenido corresponda a la extensión y tamaño máximo (`MAX_UPLOAD_MB`, 25 MB).
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
python -m app.scripts.seed                 # usuarios, contacto, enlaces, quiénes somos (borradores), línea de ayuda
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

### Día a día (ya instalado)

```bash
# Arrancar (desde la raíz del repo)
conda activate oncologico
pg_ctl -D backend/.pgdata -l backend/.pgdata/server.log -o "-p 5432 -k /tmp" start
(cd backend && uvicorn app.main:app --reload --port 8000)   # en una terminal
(cd frontend && pnpm dev)                                     # en otra; si 4321 está ocupado usa el siguiente puerto libre

# Estado
pg_ctl -D backend/.pgdata status
curl -s localhost:8000/health
(cd frontend && pnpm astro dev status)

# Parar
# uvicorn y pnpm dev: Ctrl+C en su terminal
(cd frontend && pnpm astro dev stop)   # solo si se lanzó con `pnpm dev --background` (o lo arrancó un agente)
pg_ctl -D backend/.pgdata stop -m fast # PostgreSQL sigue vivo hasta pararlo explícitamente
```

## Tests y calidad

```bash
# backend (conda activate oncologico; cd backend)
pytest                                     # casos de uso con fakes + capa HTTP (sin BD)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/oncologico_test pytest  # + integración SQL (154 en total)
ruff check . && ruff format --check .

# frontend (cd frontend)
pnpm test && pnpm typecheck && pnpm build   # 51 tests Vitest
pnpm exec playwright install chromium      # una vez, para los E2E
pnpm visual -- --base http://localhost:4321   # regresión visual contra docs/visual-baseline (local)
E2E_BASE_URL=http://localhost:4321 pnpm e2e   # E2E: documentos (subir/ver/descargar/eliminar) y permisos (admin concede → médico publica)
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
| Médica con permisos (publicaciones, documentos, enlaces) | editora@oncologico.com | Editora123! |
| Médico sin permisos (solo lectura) | medico@oncologico.com | Medico123! |

Antes de publicar el portal: validar los textos de «Quiénes somos», poner los teléfonos reales de la línea de ayuda (los actuales y los tres profesionales «(ejemplo)» son de relleno) y cambiar estas contraseñas.

## API (`/api/v1`)

- `POST /auth/login` · `GET /auth/me` (incluye los permisos efectivos)
- `GET/POST/PUT/DELETE /publications` · `POST /publications/preview` · `GET /publications/{id}/image`
- `GET/POST/PUT/DELETE /about` · `GET /about/{id}/image`
- `GET/PUT /helpline` · `GET/POST/PUT/DELETE /helpline/professionals`
- `GET/POST/PUT/DELETE /diagnostic-guides` · `/treatment-protocols` · `/diseases`
- `GET /documents` · `POST /documents` (multipart: `file` o `file_url`) · `GET|HEAD /documents/{id}/file?disposition=inline|attachment` · `DELETE /documents/{id}` · `GET /documents/upload-policy`
- `GET/POST/PUT/DELETE /interest-links` (+ `GET /interest-links/manage`) · `GET/PUT /contact`
- `GET/POST /users` · `PATCH /users/{id}` (rol, permisos, estado, contraseña) · `DELETE /users/{id}` (desactiva)

Documentación interactiva: http://localhost:8000/docs · Convenciones de código: [`.claude/CLAUDE.md`](.claude/CLAUDE.md).
