# /done — Cerrar sesión, commit y push

Cierra la sesión de trabajo. Es lo último que ejecuto antes de irme.

## Pasos

### 1. Cerrar tareas

Revisa `docs/tasks/in-progress/`:

- **Terminada** → borra el fichero. El registro queda en SESSION-LOG.md y en git.
- **A medias** → déjala en `in-progress/` y actualiza lo que falta.

### 2. Actualizar el log

Añade una entrada **arriba** de `docs/SESSION-LOG.md` con:

- Fecha y hora
- Resumen de lo hecho (lee `git diff --stat` y la conversación)
- Tareas completadas
- Pendiente (si hay)

### 3. Actualizar bugs

Los bugs de `docs/BUGS.md` corregidos en esta sesión pasan a `## Fixed` con fecha y commit.

### 4. Comprobaciones previas al push

En orden; si alguna falla, para y enséñame la salida:

- **Backend** (`conda activate oncologico`, en `backend/`): `ruff check . && ruff format --check . && pytest`. Si hay BD de pruebas, también con `TEST_DATABASE_URL=...oncologico_test`.
- **Migraciones**: si cambió algún `infrastructure/orm.py`, debe existir una migración nueva y `alembic check` debe decir "No new upgrade operations detected".
- **Frontend** (en `frontend/`): `pnpm typecheck && pnpm test && pnpm build`.
- **Visual**: si el diff toca `frontend/src/styles/`, `components/` o `layouts/`, ejecuta `/visual` y señala cualquier pantalla con >3 % de diferencia que no esté justificada.
- **Roles**: si el diff toca permisos, comprueba que `frontend/src/shared/auth/roles.ts` y `backend/app/shared/domain/actor.py` siguen siendo espejo.

### 5. Commit

- `git add -A` (docs/ está ignorado: la memoria no se commitea)
- Muéstrame la lista de ficheros
- Propón un mensaje en conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`)
- **Pide mi aprobación antes de hacer commit**
- Tras aprobarlo: `git commit` y `git push`

### 6. Resumen

Una línea: qué se entregó, en qué rama, cuántos ficheros.
