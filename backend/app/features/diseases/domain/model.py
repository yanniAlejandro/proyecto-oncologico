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
    async def update(self, disease_id: UUID, changes: dict[str, object]) -> Disease | None: ...
    async def usage(self, disease_id: UUID) -> int: ...  # nº de guías y protocolos que la usan
    async def delete(self, disease_id: UUID) -> bool: ...
