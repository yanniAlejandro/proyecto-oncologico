from urllib.parse import urlparse
from uuid import UUID, uuid4

from app.features.documents.domain.file_policy import kind_for, sanitize_filename, validate_upload
from app.features.documents.domain.model import (
    Disposition,
    Document,
    DocumentRepository,
    FileStorage,
    FileToServe,
    NewDocument,
)
from app.shared.domain.actor import CONTENT_MANAGERS, Actor, require
from app.shared.domain.result import AppError, Err, Ok, Result

NOT_FOUND = "Documento no encontrado"


class ListDocuments:
    """El repositorio es público: cualquiera lista, ve y descarga."""

    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    async def __call__(self, search: str | None = None) -> list[Document]:
        return await self._documents.list(search.strip() or None if search else None)


class UploadDocument:
    def __init__(self, documents: DocumentRepository, storage: FileStorage, max_bytes: int) -> None:
        self._documents = documents
        self._storage = storage
        self._max_bytes = max_bytes

    async def __call__(
        self, actor: Actor | None, *, title: str, description: str | None, filename: str, data: bytes
    ) -> Result[Document]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        file_name = sanitize_filename(filename)
        if isinstance(check := validate_upload(file_name, data, self._max_bytes), Err):
            return check
        kind = check.value
        key = f"{uuid4().hex}{kind.extension}"
        self._storage.save(key, data)
        try:
            doc = await self._documents.add(
                NewDocument(
                    title=title.strip(),
                    description=(description or "").strip() or None,
                    file_name=file_name,
                    file_type=kind.label,
                    uploaded_by=auth.value.id,
                    storage_key=key,
                    size_bytes=len(data),
                )
            )
        except Exception:
            self._storage.delete(key)  # no dejar ficheros huérfanos
            raise
        return Ok(doc)


class AddDocumentLink:
    """Documento que apunta a una URL externa (sin fichero almacenado)."""

    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    async def __call__(self, actor: Actor | None, *, title: str, description: str | None, url: str) -> Result[Document]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return Err(AppError.invalid("La URL debe empezar por http:// o https://"))
        file_name = sanitize_filename(parsed.path.rsplit("/", 1)[-1] or parsed.netloc)
        kind = kind_for(file_name)
        return Ok(
            await self._documents.add(
                NewDocument(
                    title=title.strip(),
                    description=(description or "").strip() or None,
                    file_name=file_name,
                    file_type=kind.label if kind else "ENLACE",
                    uploaded_by=auth.value.id,
                    file_url=url.strip(),
                )
            )
        )


class GetDocumentFile:
    def __init__(self, documents: DocumentRepository, storage: FileStorage) -> None:
        self._documents = documents
        self._storage = storage

    async def __call__(self, doc_id: UUID, disposition: Disposition) -> Result[FileToServe]:
        doc = await self._documents.get(doc_id)
        if doc is None:
            return Err(AppError.not_found(NOT_FOUND))
        if doc.storage_key is None:
            return Err(AppError.not_found("Este documento es un enlace externo y no tiene archivo almacenado"))
        path = self._storage.path(doc.storage_key)
        kind = kind_for(doc.file_name)
        if path is None or kind is None:
            return Err(AppError.not_found("El archivo no está disponible"))
        # Lo que no se puede previsualizar con seguridad se fuerza a descarga.
        if disposition is Disposition.INLINE and not kind.previewable:
            disposition = Disposition.ATTACHMENT
        return Ok(FileToServe(path=path, file_name=doc.file_name, media_type=kind.media_type, disposition=disposition))


class DeleteDocument:
    def __init__(self, documents: DocumentRepository, storage: FileStorage) -> None:
        self._documents = documents
        self._storage = storage

    async def __call__(self, actor: Actor | None, doc_id: UUID) -> Result[None]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        doc = await self._documents.get(doc_id)
        if doc is None or not await self._documents.delete(doc_id):
            return Err(AppError.not_found(NOT_FOUND))
        if doc.storage_key:
            self._storage.delete(doc.storage_key)
        return Ok(None)
