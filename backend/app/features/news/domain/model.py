from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class News:
    id: UUID
    title: str
    summary: str | None
    content: str
    is_published: bool
    created_at: datetime
    updated_at: datetime
    author_name: str | None = None


@dataclass(frozen=True, slots=True)
class NewsDraft:
    title: str
    content: str
    summary: str | None = None
    is_published: bool = True


EDITABLE_FIELDS = frozenset({"title", "summary", "content", "is_published"})


class NewsRepository(Protocol):
    async def list(self, *, published_only: bool, search: str | None) -> list[News]: ...
    async def get(self, news_id: UUID, *, published_only: bool) -> News | None: ...
    async def add(self, draft: NewsDraft, author_id: UUID) -> News: ...
    async def update(self, news_id: UUID, changes: dict[str, object]) -> News | None: ...
    async def delete(self, news_id: UUID) -> bool: ...
