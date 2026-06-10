from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.diagnostic_guide import DiagnosticGuide
from app.models.disease import Disease
from app.models.user import User, UserRole
from app.schemas.common import GuideCreate, GuideOut, GuideUpdate

router = APIRouter()


def to_guide_out(item: DiagnosticGuide) -> GuideOut:
    return GuideOut(
        id=str(item.id),
        disease_id=str(item.disease_id),
        disease_name=item.disease.name,
        title=item.title,
        content=item.content,
        author_name=item.author.full_name if item.author else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[GuideOut])
async def list_guides(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    search: str | None = Query(None),
):
    if user.role not in (UserRole.ADMINISTRADOR, UserRole.ENCARGADO, UserRole.MEDICO):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")

    query = select(DiagnosticGuide).order_by(DiagnosticGuide.title)
    if search:
        pattern = f"%{search}%"
        query = query.join(Disease).where(
            or_(DiagnosticGuide.title.ilike(pattern), Disease.name.ilike(pattern), DiagnosticGuide.content.ilike(pattern))
        )
    result = await db.execute(query)
    return [to_guide_out(g) for g in result.scalars().unique().all()]


@router.get("/{guide_id}", response_model=GuideOut)
async def get_guide(
    guide_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role not in (UserRole.ADMINISTRADOR, UserRole.ENCARGADO, UserRole.MEDICO):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")

    result = await db.execute(select(DiagnosticGuide).where(DiagnosticGuide.id == guide_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guía no encontrada")
    return to_guide_out(item)


@router.post("", response_model=GuideOut, status_code=status.HTTP_201_CREATED)
async def create_guide(
    payload: GuideCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    disease = await db.get(Disease, UUID(payload.disease_id))
    if disease is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enfermedad no encontrada")

    item = DiagnosticGuide(
        disease_id=disease.id,
        title=payload.title,
        content=payload.content,
        created_by=user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return to_guide_out(item)


@router.put("/{guide_id}", response_model=GuideOut)
async def update_guide(
    guide_id: UUID,
    payload: GuideUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(DiagnosticGuide).where(DiagnosticGuide.id == guide_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guía no encontrada")

    data = payload.model_dump(exclude_unset=True)
    if "disease_id" in data:
        disease = await db.get(Disease, UUID(data.pop("disease_id")))
        if disease is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enfermedad no encontrada")
        item.disease_id = disease.id
    for key, value in data.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return to_guide_out(item)


@router.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guide(
    guide_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(DiagnosticGuide).where(DiagnosticGuide.id == guide_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guía no encontrada")
    await db.delete(item)
    await db.commit()
