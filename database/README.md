# database/ (heredado)

Scripts SQL de la versión original. **Ya no son la fuente de verdad del esquema**: lo son los modelos ORM
(`backend/app/features/*/infrastructure/orm.py`) y las migraciones de `backend/alembic/versions/`.

- `schema.sql` ≈ migración `0001`. Una BD creada con él se adopta con `alembic stamp 0001 && alembic upgrade head`.
- `seed.sql` → sustituido por `python -m app.scripts.seed`.
- `base_de_datos_oncologico.sql` es un volcado `pg_dump` en formato custom (restaurar con `pg_restore`).
