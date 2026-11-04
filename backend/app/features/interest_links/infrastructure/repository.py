from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.interest_links.domain.model import InterestLink
from app.features.interest_links.infrastructure.orm import InterestLinkRow


def to_domain(r: InterestLinkRow) -> InterestLink:
    return InterestLink(
        id=r.id, title=r.title, url=r.url, description=r.description, sort_order=r.sort_order, is_active=r.is_active
    )


class SqlInterestLinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_active(self) -> list[InterestLink]:
        q = select(InterestLinkRow).where(InterestLinkRow.is_active.is_(True)).order_by(InterestLinkRow.sort_order)
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def add(self, data: dict[str, object]) -> InterestLink:
        row = InterestLinkRow(**data)
        self._s.add(row)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)

    async def update(self, link_id: UUID, changes: dict[str, object]) -> InterestLink | None:
        row = await self._s.get(InterestLinkRow, link_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)

    async def delete(self, link_id: UUID) -> bool:
        row = await self._s.get(InterestLinkRow, link_id)
        if row is None:
            return False
        await self._s.delete(row)
        await self._s.commit()
        return True
