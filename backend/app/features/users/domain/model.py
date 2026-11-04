from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.domain.actor import Role


@dataclass(slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    role: Role
    password_hash: str
    is_active: bool = True
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class NewUser:
    email: str
    full_name: str
    role: Role
    password_hash: str


def normalize_email(email: str) -> str:
    return email.strip().lower()
