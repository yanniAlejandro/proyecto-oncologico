from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.features.documents.domain.file_policy import kind_for


@dataclass(frozen=True, slots=True)
class Document:
    id: UUID
    title: str
    description: str | None
    file_name: str
    created_at: datetime
    file_type: str | None = None
    file_url: str | None = None  # enlace externo (documentos heredados)
    storage_key: str | None = None  # fichero subido al almacenamiento
    size_bytes: int | None = None
    uploader_name: str | None = None

    @property
    def has_stored_file(self) -> bool:
        return self.storage_key is not None

    @property
    def is_previewable(self) -> bool:
        kind = kind_for(self.file_name)
        return self.has_stored_file and kind is not None and kind.previewable


@dataclass(frozen=True, slots=True)
class NewDocument:
    title: str
    description: str | None
    file_name: str
    file_type: str | None
    uploaded_by: UUID
    file_url: str | None = None
    storage_key: str | None = None
    size_bytes: int | None = None


class Disposition(StrEnum):
    INLINE = "inline"
    ATTACHMENT = "attachment"


@dataclass(frozen=True, slots=True)
class FileToServe:
    path: Path
    file_name: str
    media_type: str
    disposition: Disposition


class DocumentRepository(Protocol):
    async def list(self, search: str | None) -> list[Document]: ...
    async def get(self, doc_id: UUID) -> Document | None: ...
    async def add(self, new: NewDocument) -> Document: ...
    async def delete(self, doc_id: UUID) -> bool: ...


class FileStorage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def path(self, key: str) -> Path | None: ...
    def delete(self, key: str) -> None: ...
