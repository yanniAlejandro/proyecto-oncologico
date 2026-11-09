from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.publications.domain.model import NewPublication, Publication
from app.features.publications.infrastructure.orm import PublicationRow


def to_domain(row: PublicationRow) -> Publication:
    return Publication(
        id=row.id,
        title=row.title,
        url=row.url,
        description=row.description,
        image_key=row.image_key,
        created_at=row.created_at,
        updated_at=row.updated_at,
        author_name=row.author.full_name if row.author else None,
    )


class SqlPublicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _load(self, publication_id: UUID) -> PublicationRow | None:
        stmt = (
            select(PublicationRow).where(PublicationRow.id == publication_id).execution_options(populate_existing=True)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list(self, search: str | None) -> list[Publication]:
        q = select(PublicationRow).order_by(PublicationRow.created_at.desc())
        if search:
            p = f"%{search}%"
            q = q.where(
                or_(PublicationRow.title.ilike(p), PublicationRow.description.ilike(p), PublicationRow.url.ilike(p))
            )
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get(self, publication_id: UUID) -> Publication | None:
        row = await self._load(publication_id)
        return to_domain(row) if row else None

    async def add(self, new: NewPublication) -> Publication:
        row = PublicationRow(
            title=new.title,
            url=new.url,
            description=new.description,
            image_key=new.image_key,
            author_id=new.author_id,
        )
        self._s.add(row)
        await self._s.commit()
        publication_id = row.id
        loaded = await self._load(publication_id)
        assert loaded is not None
        return to_domain(loaded)

    async def update(self, publication_id: UUID, changes: dict[str, object]) -> Publication | None:
        row = await self._load(publication_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        loaded = await self._load(publication_id)
        return to_domain(loaded) if loaded else None

    async def delete(self, publication_id: UUID) -> bool:
        result = await self._s.execute(delete(PublicationRow).where(PublicationRow.id == publication_id))
        await self._s.commit()
        return bool(result.rowcount)
