"""Guías de diagnóstico y protocolos de tratamiento.

Comparten forma (enfermedad + título + contenido); difieren en quién puede leer:
las guías son solo para personal autenticado, los protocolos son públicos.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.shared.domain.actor import GUIDE_READERS, Role


class ContentKind(StrEnum):
    GUIDE = "guide"
    PROTOCOL = "protocol"

    @property
    def readers(self) -> frozenset[Role] | None:
        """Roles con lectura; ``None`` = público."""
        return GUIDE_READERS if self is ContentKind.GUIDE else None

    @property
    def not_found_message(self) -> str:
        return "Guía no encontrada" if self is ContentKind.GUIDE else "Protocolo no encontrado"


@dataclass(frozen=True, slots=True)
class ClinicalDoc:
    id: UUID
    disease_id: UUID
    disease_name: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author_name: str | None = None


@dataclass(frozen=True, slots=True)
class ClinicalDraft:
    disease_id: UUID
    title: str
    content: str


EDITABLE_FIELDS = frozenset({"disease_id", "title", "content"})


class ClinicalContentRepository(Protocol):
    async def list(self, search: str | None) -> list[ClinicalDoc]: ...
    async def get(self, doc_id: UUID) -> ClinicalDoc | None: ...
    async def add(self, draft: ClinicalDraft, author_id: UUID) -> ClinicalDoc: ...
    async def update(self, doc_id: UUID, changes: dict[str, object]) -> ClinicalDoc | None: ...
    async def delete(self, doc_id: UUID) -> bool: ...
