from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ContactInfo:
    id: UUID
    organization_name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    schedule: str | None = None
    map_url: str | None = None


EDITABLE_FIELDS = frozenset({"organization_name", "address", "phone", "email", "schedule", "map_url"})
DEFAULT_ORGANIZATION = "Hospital Oncológico de La Habana"


class ContactRepository(Protocol):
    async def get(self) -> ContactInfo | None: ...
    async def upsert(self, changes: dict[str, object]) -> ContactInfo: ...
