from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InterestLink:
    id: UUID
    title: str
    url: str
    description: str | None
    sort_order: int
    is_active: bool


EDITABLE_FIELDS = frozenset({"title", "url", "description", "sort_order", "is_active"})


class InterestLinkRepository(Protocol):
    async def list_active(self) -> list[InterestLink]: ...
    async def add(self, data: dict[str, object]) -> InterestLink: ...
    async def update(self, link_id: UUID, changes: dict[str, object]) -> InterestLink | None: ...
    async def delete(self, link_id: UUID) -> bool: ...
