"""Quién ejecuta un caso de uso y qué puede hacer (reglas de permisos puras).

Dos roles: administrador (todo) y médico. Un médico, por defecto, solo ve y descarga;
para gestionar una sección necesita que un administrador le conceda ese permiso.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from app.shared.domain.result import AppError, Err, Ok, Result


class Role(StrEnum):
    ADMINISTRADOR = "administrador"
    MEDICO = "medico"


class Section(StrEnum):
    """Secciones gestionables. Con el permiso, CRUD completo (también sobre lo de otros)."""

    PUBLICACIONES = "publicaciones"
    GUIAS = "guias"
    PROTOCOLOS = "protocolos"
    ENFERMEDADES = "enfermedades"
    DOCUMENTOS = "documentos"
    ENLACES = "enlaces"
    QUIENES_SOMOS = "quienes_somos"
    LINEA_AYUDA = "linea_ayuda"


ALL_SECTIONS = frozenset(Section)


@dataclass(frozen=True, slots=True)
class Actor:
    """Usuario autenticado. Un visitante anónimo se representa con ``None``."""

    id: UUID
    role: Role
    full_name: str = ""
    permissions: frozenset[Section] = field(default_factory=frozenset)

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMINISTRADOR

    def can(self, section: Section) -> bool:
        return self.is_admin or section in self.permissions

    @property
    def effective_permissions(self) -> frozenset[Section]:
        return ALL_SECTIONS if self.is_admin else self.permissions


def normalize_permissions(values: Iterable[str | Section]) -> frozenset[Section]:
    """Valores desconocidos se descartan (p. ej. una sección eliminada)."""
    valid = {s.value for s in Section}
    return frozenset(Section(v) for v in values if str(v) in valid)


def require_user(actor: Actor | None) -> Result[Actor]:
    """Cualquier usuario con sesión (médico o admin)."""
    return Ok(actor) if actor is not None else Err(AppError.unauthenticated())


def require_admin(actor: Actor | None) -> Result[Actor]:
    if actor is None:
        return Err(AppError.unauthenticated())
    return Ok(actor) if actor.is_admin else Err(AppError.forbidden())


def require_section(actor: Actor | None, section: Section) -> Result[Actor]:
    """Admin, o médico con el permiso de esa sección; si no, 401 o 403."""
    if actor is None:
        return Err(AppError.unauthenticated())
    return Ok(actor) if actor.can(section) else Err(AppError.forbidden())
