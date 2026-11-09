# /brief — Resumen de inicio de sesión

Lee la memoria del proyecto y dame un resumen breve para retomar el trabajo.

## Pasos

1. **Tablero** — Lista los ficheros de `docs/tasks/in-progress/` y `docs/tasks/todo/`. Lee cada `.md` para sacar título y prioridad. Primero in-progress, luego todo ordenado por prioridad.
2. **Última sesión** — Lee `docs/SESSION-LOG.md`, toma la entrada más reciente y resume qué se hizo y qué quedó pendiente.
3. **Git** — `git log --oneline -5` y `git status`.
4. **Bugs abiertos** — Lee `docs/BUGS.md` y lista los `## Open`. Para cada uno, mira el fichero referenciado y comprueba si sigue existiendo; si ya está arreglado, actualiza BUGS.md en silencio.
5. **Decisiones recientes** — Ficheros de `docs/decisions/` de los últimos 7 días.
6. **Ramas** — `git branch --sort=committerdate`, de la más antigua a la más reciente, sin la actual.
7. **Entorno** — Comprueba en una línea si PostgreSQL (conda `oncologico`, `backend/.pgdata`) y los servidores (8000 API, 4321 web) están levantados (`pg_ctl status`, `curl -s localhost:8000/health`).

## Formato

```
## Resumen de sesión — {fecha}

### Tablero
🔨 En curso: {tarea} (prioridad)
📋 Pendiente: {tarea} (prioridad)

**Última sesión:** {fecha} — {resumen}
**Bugs abiertos:** {n} ({lista breve con ficheros})
**Git:** {rama} · {cambios sin commit} · último commit: {hash} {msg}
**Ramas (más antiguas primero):** {rama1}, {rama2}, ...
**Entorno:** BD {ok/parada} · API {ok/parada} · Web {ok/parada}
```

Que se lea en 15 segundos.
