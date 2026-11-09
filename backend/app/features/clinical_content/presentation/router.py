"""Dos routers con el mismo contrato: /diagnostic-guides y /treatment-protocols."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.clinical_content.application import use_cases as uc
from app.features.clinical_content.domain.model import (
    ClinicalContentRepository,
    ClinicalDoc,
    ClinicalDraft,
    ContentKind,
)
from app.features.clinical_content.infrastructure.repository import SqlClinicalContentRepository
from app.features.diseases.presentation.deps import Diseases
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap


class ClinicalCreate(BaseModel):
    disease_id: UUID
    title: str = Field(min_length=3)
    content: str = Field(min_length=10)


class ClinicalUpdate(BaseModel):
    disease_id: UUID | None = None
    title: str | None = Field(None, min_length=3)
    content: str | None = Field(None, min_length=10)


class ClinicalOut(BaseModel):
    id: str
    disease_id: str
    disease_name: str
    title: str
    content: str
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, d: ClinicalDoc) -> "ClinicalOut":
        return cls(
            id=str(d.id),
            disease_id=str(d.disease_id),
            disease_name=d.disease_name,
            title=d.title,
            content=d.content,
            author_name=d.author_name,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


def repository_provider(kind: ContentKind) -> Callable[..., ClinicalContentRepository]:
    def provide(session: Annotated[AsyncSession, Depends(get_session)]) -> ClinicalContentRepository:
        return SqlClinicalContentRepository(session, kind)

    provide.__name__ = f"get_{kind.value}_repository"
    return provide


GUIDE_REPOSITORY = repository_provider(ContentKind.GUIDE)
PROTOCOL_REPOSITORY = repository_provider(ContentKind.PROTOCOL)


def build_router(kind: ContentKind, provider: Callable[..., ClinicalContentRepository]) -> APIRouter:
    router = APIRouter()
    Repo = Annotated[ClinicalContentRepository, Depends(provider)]

    @router.get("", response_model=list[ClinicalOut])
    async def list_docs(repo: Repo, actor: CurrentActor, search: str | None = Query(None)):
        return [ClinicalOut.of(d) for d in unwrap(await uc.ListClinicalDocs(kind, repo)(actor, search))]

    @router.get("/{doc_id}", response_model=ClinicalOut)
    async def get_doc(doc_id: UUID, repo: Repo, actor: CurrentActor):
        return ClinicalOut.of(unwrap(await uc.GetClinicalDoc(kind, repo)(actor, doc_id)))

    @router.post("", response_model=ClinicalOut, status_code=status.HTTP_201_CREATED)
    async def create_doc(payload: ClinicalCreate, repo: Repo, diseases: Diseases, actor: CurrentActor):
        draft = ClinicalDraft(**payload.model_dump())
        return ClinicalOut.of(unwrap(await uc.CreateClinicalDoc(kind, repo, diseases)(actor, draft)))

    @router.put("/{doc_id}", response_model=ClinicalOut)
    async def update_doc(doc_id: UUID, payload: ClinicalUpdate, repo: Repo, diseases: Diseases, actor: CurrentActor):
        changes = payload.model_dump(exclude_unset=True)
        return ClinicalOut.of(unwrap(await uc.UpdateClinicalDoc(kind, repo, diseases)(actor, doc_id, changes)))

    @router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_doc(doc_id: UUID, repo: Repo, actor: CurrentActor):
        unwrap(await uc.DeleteClinicalDoc(kind, repo)(actor, doc_id))

    return router


guides_router = build_router(ContentKind.GUIDE, GUIDE_REPOSITORY)
protocols_router = build_router(ContentKind.PROTOCOL, PROTOCOL_REPOSITORY)
