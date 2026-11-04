"""Quién ejecuta un caso de uso y qué puede hacer (reglas de rol puras)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.shared.domain.result import AppError, Err, Ok, Result


class Role(StrEnum):
    ADMINISTRADOR = "administrador"
    ENCARGADO = "encargado"
    MEDICO = "medico"


@dataclass(frozen=True, slots=True)
class Actor:
    """Usuario autenticado. Un visitante anónimo se representa con ``None``."""

    id: UUID
    role: Role
    full_name: str = ""


CONTENT_MANAGERS = frozenset({Role.ADMINISTRADOR, Role.ENCARGADO})
GUIDE_READERS = frozenset({Role.ADMINISTRADOR, Role.ENCARGADO, Role.MEDICO})
ADMINS = frozenset({Role.ADMINISTRADOR})


def require(actor: Actor | None, allowed: frozenset[Role]) -> Result[Actor]:
    """Devuelve el actor si tiene uno de los roles; si no, 401 o 403."""
    if actor is None:
        return Err(AppError.unauthenticated())
    if actor.role not in allowed:
        return Err(AppError.forbidden())
    return Ok(actor)


def can_manage_content(actor: Actor | None) -> bool:
    return actor is not None and actor.role in CONTENT_MANAGERS
