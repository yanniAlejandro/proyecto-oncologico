from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.about.domain.model import AboutSection, NewAboutSection
from app.features.about.infrastructure.orm import AboutSectionRow


def to_domain(row: AboutSectionRow) -> AboutSection:
    return AboutSection(
        id=row.id,
        slug=row.slug,
        title=row.title,
        body=row.body,
        sort_order=row.sort_order,
        updated_at=row.updated_at,
        image_key=row.image_key,
    )


class SqlAboutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _load(self, section_id: UUID) -> AboutSectionRow | None:
        stmt = select(AboutSectionRow).where(AboutSectionRow.id == section_id).execution_options(populate_existing=True)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list(self) -> list[AboutSection]:
        q = select(AboutSectionRow).order_by(AboutSectionRow.sort_order, AboutSectionRow.title)
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get(self, section_id: UUID) -> AboutSection | None:
        row = await self._load(section_id)
        return to_domain(row) if row else None

    async def slug_exists(self, slug: str, exclude: UUID | None = None) -> bool:
        q = select(AboutSectionRow.id).where(AboutSectionRow.slug == slug)
        if exclude is not None:
            q = q.where(AboutSectionRow.id != exclude)
        return (await self._s.execute(q)).first() is not None

    async def add(self, new: NewAboutSection) -> AboutSection:
        row = AboutSectionRow(
            slug=new.slug, title=new.title, body=new.body, sort_order=new.sort_order, image_key=new.image_key
        )
        self._s.add(row)
        await self._s.commit()
        section_id = row.id
        loaded = await self._load(section_id)
        assert loaded is not None
        return to_domain(loaded)

    async def update(self, section_id: UUID, changes: dict[str, object]) -> AboutSection | None:
        row = await self._load(section_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        loaded = await self._load(section_id)
        return to_domain(loaded) if loaded else None

    async def delete(self, section_id: UUID) -> bool:
        result = await self._s.execute(delete(AboutSectionRow).where(AboutSectionRow.id == section_id))
        await self._s.commit()
        return bool(result.rowcount)
