from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.document import Document
from app.models.user import User, UserRole
from app.schemas.common import DocumentCreate, DocumentOut

router = APIRouter()


def to_document_out(item: Document) -> DocumentOut:
    return DocumentOut(
        id=str(item.id),
        title=item.title,
        description=item.description,
        file_name=item.file_name,
        file_url=item.file_url,
        file_type=item.file_type,
        uploader_name=item.uploader.full_name if item.uploader else None,
        created_at=item.created_at,
    )


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
):
    query = select(Document).order_by(Document.created_at.desc())
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Document.title.ilike(pattern), Document.description.ilike(pattern)))
    result = await db.execute(query)
    return [to_document_out(d) for d in result.scalars().all()]


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    item = Document(**payload.model_dump(), uploaded_by=user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return to_document_out(item)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
    await db.delete(item)
    await db.commit()
