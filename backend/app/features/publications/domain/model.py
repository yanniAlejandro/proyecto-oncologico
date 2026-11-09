"""Publicaciones: enlaces que comparte el hospital (título + URL + descripción + imagen opcional)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlparse
from uuid import UUID

MAX_URL_LENGTH = 1000
EDITABLE_FIELDS = frozenset({"title", "url", "description"})


@dataclass(frozen=True, slots=True)
class Publication:
    id: UUID
    title: str
    url: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    image_key: str | None = None
    author_name: str | None = None

    @property
    def has_image(self) -> bool:
        return self.image_key is not None

    @property
    def domain(self) -> str:
        return (urlparse(self.url).hostname or "").removeprefix("www.")


@dataclass(frozen=True, slots=True)
class NewPublication:
    title: str
    url: str
    description: str | None
    author_id: UUID
    image_key: str | None = None


@dataclass(frozen=True, slots=True)
class LinkPreview:
    """Lo que se lee de las etiquetas Open Graph de la página enlazada."""

    url: str
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    site_name: str | None = None

    @property
    def is_empty(self) -> bool:
        return not (self.title or self.description or self.image_url)


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.hostname) and len(url) <= MAX_URL_LENGTH


class PublicationRepository(Protocol):
    async def list(self, search: str | None) -> list[Publication]: ...
    async def get(self, publication_id: UUID) -> Publication | None: ...
    async def add(self, new: NewPublication) -> Publication: ...
    async def update(self, publication_id: UUID, changes: dict[str, object]) -> Publication | None: ...
    async def delete(self, publication_id: UUID) -> bool: ...


class LinkPreviewer(Protocol):
    """Descarga páginas e imágenes de Internet. ``None`` si no se pudo (red, SSRF, tamaño, formato)."""

    async def preview(self, url: str) -> LinkPreview | None: ...
    async def fetch_image(self, url: str) -> bytes | None: ...
