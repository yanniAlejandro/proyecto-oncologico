from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Disease:
    id: UUID
    name: str
    description: str | None = None


class DiseaseRepository(Protocol):
    async def list(self, search: str | None = None) -> list[Disease]: ...
    async def get(self, disease_id: UUID) -> Disease | None: ...
    async def get_by_name(self, name: str) -> Disease | None: ...
    async def add(self, name: str, description: str | None) -> Disease: ...
