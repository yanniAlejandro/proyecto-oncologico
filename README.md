# Portal Oncológico

Sistema web monorepo con **React + TypeScript** (frontend), **FastAPI** (backend) y **PostgreSQL** (base de datos).

## Estructura

```
proyecto-oncologico/
├── frontend/          # React + TypeScript (Vite)
├── backend/           # FastAPI
├── database/          # Scripts SQL
└── .cursor/rules/     # Reglas de Cursor
```

## Vistas

| Vista | Ruta | Acceso |
|-------|------|--------|
| Noticias (landing) | `/` | Público. Login desde aquí |
| Guías de diagnóstico | `/guias-diagnostico` | Médico, encargado, admin |
| Protocolos de tratamiento | `/protocolos-tratamiento` | Público (lectura) |
| Repositorio de documentos | `/documentos` | Público |
| Enlaces de interés | `/enlaces` | Público |
| Contacto | `/contacto` | Público |
| Gestión de noticias | `/gestion/noticias` | Encargado, admin |
| Gestión de usuarios | `/gestion/usuarios` | Admin |

## Roles

| Rol | Permisos |
|-----|----------|
| **Administrador** | Acceso total. Crear cuentas de médicos |
| **Encargado** | CRUD noticias, guías de diagnóstico y protocolos de tratamiento |
| **Médico** | Leer guías de diagnóstico |
| **Visitante** | Leer protocolos de tratamiento y contenido público |

## Requisitos

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+

## Instalación

### 1. Base de datos

```bash
# Crear la base de datos
psql -U postgres -c "CREATE DATABASE oncologico;"

# Ejecutar el esquema
psql -U postgres -d oncologico -f database/schema.sql
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

# Crear usuarios de prueba
python -m app.scripts.seed

# Cargar guías, protocolos y documentos de ejemplo
python -m app.scripts.seed_clinical

# Iniciar servidor
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Abrir http://localhost:5173

## Usuarios de prueba

| Rol | Correo | Contraseña |
|-----|--------|------------|
| Administrador | admin@oncologico.com | Admin123! |
| Encargado | encargado@oncologico.com | Encargado123! |
| Médico | medico@oncologico.com | Medico123! |

## API

Documentación interactiva: http://localhost:8000/docs

Endpoints principales bajo `/api/v1`:
- `POST /auth/login` — Iniciar sesión
- `GET /auth/me` — Usuario actual
- `GET/POST/PUT/DELETE /news` — Noticias
- `GET/POST/PUT/DELETE /diagnostic-guides` — Guías de diagnóstico
- `GET/POST/PUT/DELETE /treatment-protocols` — Protocolos (lectura pública)
- `GET/POST/DELETE /documents` — Documentos
- `GET /interest-links` — Enlaces de interés
- `GET /contact` — Contacto
- `GET/POST /users` — Gestión de usuarios (admin)
