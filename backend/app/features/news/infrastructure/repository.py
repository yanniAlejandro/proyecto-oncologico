from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.news.domain.model import News, NewsDraft
from app.features.news.infrastructure.orm import NewsRow


def to_domain(row: NewsRow) -> News:
    return News(
        id=row.id,
        title=row.title,
        summary=row.summary,
        content=row.content,
        is_published=row.is_published,
        created_at=row.created_at,
        updated_at=row.updated_at,
        author_name=row.author.full_name if row.author else None,
    )


class SqlNewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list(self, *, published_only: bool, search: str | None) -> list[News]:
        q = select(NewsRow).order_by(NewsRow.created_at.desc())
        if published_only:
            q = q.where(NewsRow.is_published.is_(True))
        if search:
            p = f"%{search}%"
            q = q.where(or_(NewsRow.title.ilike(p), NewsRow.summary.ilike(p), NewsRow.content.ilike(p)))
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get(self, news_id: UUID, *, published_only: bool) -> News | None:
        q = select(NewsRow).where(NewsRow.id == news_id)
        if published_only:
            q = q.where(NewsRow.is_published.is_(True))
        row = (await self._s.execute(q)).scalar_one_or_none()
        return to_domain(row) if row else None

    async def add(self, draft: NewsDraft, author_id: UUID) -> News:
        row = NewsRow(
            title=draft.title,
            summary=draft.summary,
            content=draft.content,
            is_published=draft.is_published,
            author_id=author_id,
        )
        self._s.add(row)
        await self._s.commit()
        return await self._reload(row.id)

    async def update(self, news_id: UUID, changes: dict[str, object]) -> News | None:
        row = await self._s.get(NewsRow, news_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        return await self._reload(news_id)

    async def delete(self, news_id: UUID) -> bool:
        row = await self._s.get(NewsRow, news_id)
        if row is None:
            return False
        await self._s.delete(row)
        await self._s.commit()
        return True

    async def _reload(self, news_id: UUID) -> News:
        self._s.expire_all()
        item = await self.get(news_id, published_only=False)
        assert item is not None
        return item
