from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.news import News
from app.models.user import User, UserRole
from app.schemas.common import NewsCreate, NewsOut, NewsUpdate

router = APIRouter()


def to_news_out(item: News) -> NewsOut:
    return NewsOut(
        id=str(item.id),
        title=item.title,
        summary=item.summary,
        content=item.content,
        author_name=item.author.full_name if item.author else None,
        is_published=item.is_published,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[NewsOut])
async def list_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(None),
):
    query = select(News).where(News.is_published.is_(True)).order_by(News.created_at.desc())
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(News.title.ilike(pattern), News.summary.ilike(pattern), News.content.ilike(pattern)))
    result = await db.execute(query)
    return [to_news_out(n) for n in result.scalars().all()]


@router.get("/manage", response_model=list[NewsOut])
async def list_news_manage(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
    search: str | None = Query(None),
):
    query = select(News).order_by(News.created_at.desc())
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(News.title.ilike(pattern), News.summary.ilike(pattern)))
    result = await db.execute(query)
    return [to_news_out(n) for n in result.scalars().all()]


@router.get("/{news_id}", response_model=NewsOut)
async def get_news(news_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(News).where(News.id == news_id, News.is_published.is_(True)))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada")
    return to_news_out(item)


@router.post("", response_model=NewsOut, status_code=status.HTTP_201_CREATED)
async def create_news(
    payload: NewsCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    item = News(**payload.model_dump(), author_id=user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return to_news_out(item)


@router.put("/{news_id}", response_model=NewsOut)
async def update_news(
    news_id: UUID,
    payload: NewsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(News).where(News.id == news_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return to_news_out(item)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.ADMINISTRADOR, UserRole.ENCARGADO))],
):
    result = await db.execute(select(News).where(News.id == news_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada")
    await db.delete(item)
    await db.commit()
