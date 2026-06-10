from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.disease import Disease
from app.models.treatment_protocol import TreatmentProtocol
from app.models.user import User, UserRole
from app.schemas.common import ProtocolCreate, ProtocolOut, ProtocolUpdate

router = APIRouter()


def to_protocol_out(item: TreatmentProtocol) -> ProtocolOut:
    return ProtocolOut(
        id=str(item.id),
        disease_id=str(item.disease_id),
        disease_name=item.disease.name,
        title=item.title,
        content=item.content,
        author_name=item.author.full_name if item.author else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[ProtocolOut])
async def list_protocols(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
):
    query = select(TreatmentProtocol).order_by(TreatmentProtocol.title)
    if search:
        pattern = f"%{search}%"
        query = query.join(Disease).where(
            or_(TreatmentProtocol.title.ilike(pattern), Disease.name.ilike(pattern), TreatmentProtocol.content.ilike(pattern))
        )
    result = await db.execute(query)
    return [to_protocol_out(p) for p in result.scalars().unique().all()]


@router.get("/{protocol_id}", response_model=ProtocolOut)
async def get_protocol(protocol_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(TreatmentProtocol).where(TreatmentProtocol.id == protocol_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocolo no encontrado")
    return to_protocol_out(item)


@router.post("", response_model=ProtocolOut, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    payload: ProtocolCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    disease = await db.get(Disease, UUID(payload.disease_id))
    if disease is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enfermedad no encontrada")

    item = TreatmentProtocol(
        disease_id=disease.id,
        title=payload.title,
        content=payload.content,
        created_by=user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return to_protocol_out(item)


@router.put("/{protocol_id}", response_model=ProtocolOut)
async def update_protocol(
    protocol_id: UUID,
    payload: ProtocolUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(TreatmentProtocol).where(TreatmentProtocol.id == protocol_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocolo no encontrado")

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
    return to_protocol_out(item)


@router.delete("/{protocol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protocol(
    protocol_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(TreatmentProtocol).where(TreatmentProtocol.id == protocol_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protocolo no encontrado")
    await db.delete(item)
    await db.commit()
