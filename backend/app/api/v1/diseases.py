from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.disease import Disease
from app.models.user import User, UserRole
from app.schemas.common import DiseaseCreate, DiseaseOut

router = APIRouter()


@router.get("", response_model=list[DiseaseOut])
async def list_diseases(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
):
    query = select(Disease).order_by(Disease.name)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Disease.name.ilike(pattern), Disease.description.ilike(pattern)))
    result = await db.execute(query)
    return [
        DiseaseOut(id=str(d.id), name=d.name, description=d.description)
        for d in result.scalars().all()
    ]


@router.post("", response_model=DiseaseOut, status_code=status.HTTP_201_CREATED)
async def create_disease(
    payload: DiseaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    disease = Disease(**payload.model_dump())
    db.add(disease)
    await db.commit()
    await db.refresh(disease)
    return DiseaseOut(id=str(disease.id), name=disease.name, description=disease.description)
