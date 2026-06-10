from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.interest_link import InterestLink
from app.models.user import User, UserRole
from app.schemas.common import InterestLinkCreate, InterestLinkOut, InterestLinkUpdate

router = APIRouter()


@router.get("", response_model=list[InterestLinkOut])
async def list_links(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(InterestLink).where(InterestLink.is_active.is_(True)).order_by(InterestLink.sort_order)
    )
    return [
        InterestLinkOut(
            id=str(l.id),
            title=l.title,
            url=l.url,
            description=l.description,
            sort_order=l.sort_order,
            is_active=l.is_active,
        )
        for l in result.scalars().all()
    ]


@router.post("", response_model=InterestLinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: InterestLinkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    link = InterestLink(**payload.model_dump())
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return InterestLinkOut(
        id=str(link.id),
        title=link.title,
        url=link.url,
        description=link.description,
        sort_order=link.sort_order,
        is_active=link.is_active,
    )


@router.put("/{link_id}", response_model=InterestLinkOut)
async def update_link(
    link_id: UUID,
    payload: InterestLinkUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(InterestLink).where(InterestLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enlace no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, key, value)
    await db.commit()
    await db.refresh(link)
    return InterestLinkOut(
        id=str(link.id),
        title=link.title,
        url=link.url,
        description=link.description,
        sort_order=link.sort_order,
        is_active=link.is_active,
    )


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(InterestLink).where(InterestLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enlace no encontrado")
    await db.delete(link)
    await db.commit()
