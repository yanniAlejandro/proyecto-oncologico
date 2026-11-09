"""«Quiénes somos»: portada del portal, en apartados ordenados (título + texto con formato básico + foto)."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

MAX_BODY = 20_000
EDITABLE_FIELDS = frozenset({"title", "body", "sort_order"})


@dataclass(frozen=True, slots=True)
class AboutSection:
    id: UUID
    slug: str
    title: str
    body: str
    sort_order: int
    updated_at: datetime
    image_key: str | None = None

    @property
    def has_image(self) -> bool:
        return self.image_key is not None


@dataclass(frozen=True, slots=True)
class NewAboutSection:
    slug: str
    title: str
    body: str
    sort_order: int
    image_key: str | None = None


def slugify(text: str) -> str:
    """Ancla del índice: «Derechos del paciente» → «derechos-del-paciente»."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:80] or "apartado"


class AboutRepository(Protocol):
    async def list(self) -> list[AboutSection]: ...
    async def get(self, section_id: UUID) -> AboutSection | None: ...
    async def slug_exists(self, slug: str, exclude: UUID | None = None) -> bool: ...
    async def add(self, new: NewAboutSection) -> AboutSection: ...
    async def update(self, section_id: UUID, changes: dict[str, object]) -> AboutSection | None: ...
    async def delete(self, section_id: UUID) -> bool: ...
