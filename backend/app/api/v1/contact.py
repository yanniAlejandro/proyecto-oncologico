from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.contact import ContactInfo
from app.models.user import User, UserRole
from app.schemas.common import ContactOut, ContactUpdate

router = APIRouter()


def to_contact_out(item: ContactInfo) -> ContactOut:
    return ContactOut(
        id=str(item.id),
        organization_name=item.organization_name,
        address=item.address,
        phone=item.phone,
        email=item.email,
        schedule=item.schedule,
        map_url=item.map_url,
    )


@router.get("", response_model=ContactOut)
async def get_contact(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(ContactInfo).limit(1))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Información de contacto no configurada")
    return to_contact_out(item)


@router.put("", response_model=ContactOut)
async def update_contact(
    payload: ContactUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR))],
):
    result = await db.execute(select(ContactInfo).limit(1))
    item = result.scalar_one_or_none()
    if item is None:
        item = ContactInfo(organization_name="Centro Oncológico")
        db.add(item)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return to_contact_out(item)
