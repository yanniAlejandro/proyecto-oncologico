from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.documents.application import use_cases as uc
from app.features.documents.domain.file_policy import ALLOWED_EXTENSIONS
from app.features.documents.domain.model import Disposition, Document, DocumentRepository, FileStorage
from app.features.documents.infrastructure.local_storage import LocalFileStorage
from app.features.documents.infrastructure.repository import SqlDocumentRepository
from app.shared.domain.result import AppError
from app.shared.infrastructure.config import settings
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import raise_http, unwrap

router = APIRouter()


def get_document_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> DocumentRepository:
    return SqlDocumentRepository(session)


def get_file_storage() -> FileStorage:
    return LocalFileStorage(settings.STORAGE_DIR)


def get_max_upload_bytes() -> int:
    return settings.max_upload_bytes


Repo = Annotated[DocumentRepository, Depends(get_document_repository)]
Storage = Annotated[FileStorage, Depends(get_file_storage)]
MaxBytes = Annotated[int, Depends(get_max_upload_bytes)]


class DocumentOut(BaseModel):
    id: str
    title: str
    description: str | None
    file_name: str
    file_type: str | None
    file_url: str | None
    size_bytes: int | None
    has_file: bool
    is_previewable: bool
    uploader_name: str | None = None
    created_at: datetime

    @classmethod
    def of(cls, d: Document) -> "DocumentOut":
        return cls(
            id=str(d.id),
            title=d.title,
            description=d.description,
            file_name=d.file_name,
            file_type=d.file_type,
            file_url=d.file_url,
            size_bytes=d.size_bytes,
            has_file=d.has_stored_file,
            is_previewable=d.is_previewable,
            uploader_name=d.uploader_name,
            created_at=d.created_at,
        )


class UploadPolicyOut(BaseModel):
    allowed_extensions: list[str]
    max_bytes: int


@router.get("", response_model=list[DocumentOut])
async def list_documents(repo: Repo, search: str | None = Query(None)):
    return [DocumentOut.of(d) for d in await uc.ListDocuments(repo)(search)]


@router.get("/upload-policy", response_model=UploadPolicyOut)
async def upload_policy(max_bytes: MaxBytes):
    return UploadPolicyOut(allowed_extensions=list(ALLOWED_EXTENSIONS), max_bytes=max_bytes)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    repo: Repo,
    storage: Storage,
    max_bytes: MaxBytes,
    actor: CurrentActor,
    title: Annotated[str, Form(min_length=3, max_length=500)],
    description: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    file_url: Annotated[str | None, Form()] = None,
):
    """Multipart: o bien ``file`` (subida) o bien ``file_url`` (enlace externo)."""
    if file is not None and file.filename:
        data = await file.read(max_bytes + 1)
        result = await uc.UploadDocument(repo, storage, max_bytes)(
            actor, title=title, description=description, filename=file.filename, data=data
        )
    elif file_url:
        result = await uc.AddDocumentLink(repo)(actor, title=title, description=description, url=file_url)
    else:
        raise_http(AppError.invalid("Adjunta un archivo o indica una URL"))
    return DocumentOut.of(unwrap(result))


@router.api_route("/{document_id}/file", methods=["GET", "HEAD"])
async def get_document_file(
    document_id: UUID, repo: Repo, storage: Storage, disposition: Disposition = Query(Disposition.ATTACHMENT)
):
    served = unwrap(await uc.GetDocumentFile(repo, storage)(document_id, disposition))
    return FileResponse(
        served.path,
        media_type=served.media_type,
        filename=served.file_name,
        content_disposition_type=served.disposition.value,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=300"},
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, repo: Repo, storage: Storage, actor: CurrentActor):
    unwrap(await uc.DeleteDocument(repo, storage)(actor, document_id))
