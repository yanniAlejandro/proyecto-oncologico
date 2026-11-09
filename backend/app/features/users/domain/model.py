from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.shared.domain.actor import Role, Section


@dataclass(slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    role: Role
    password_hash: str
    is_active: bool = True
    created_at: datetime | None = None
    permissions: frozenset[Section] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class NewUser:
    email: str
    full_name: str
    role: Role
    password_hash: str
    permissions: frozenset[Section] = frozenset()


@dataclass(frozen=True, slots=True)
class UserChanges:
    """Cambios de un admin sobre una cuenta. ``None`` = no tocar."""

    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    permissions: frozenset[Section] | None = None
    password_hash: str | None = None


def normalize_email(email: str) -> str:
    return email.strip().lower()
