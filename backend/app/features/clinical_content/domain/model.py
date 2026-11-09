"""Guías de diagnóstico y protocolos de tratamiento.

Comparten forma (enfermedad + título + contenido) y lectura (solo usuarios con sesión);
cada uno tiene su propio permiso de gestión.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.shared.domain.actor import Section


class ContentKind(StrEnum):
    GUIDE = "guide"
    PROTOCOL = "protocol"

    @property
    def section(self) -> Section:
        """Permiso necesario para gestionar este tipo de contenido."""
        return Section.GUIAS if self is ContentKind.GUIDE else Section.PROTOCOLOS

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
