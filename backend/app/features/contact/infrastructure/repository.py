from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.contact.domain.model import DEFAULT_ORGANIZATION, ContactInfo
from app.features.contact.infrastructure.orm import ContactInfoRow


def to_domain(r: ContactInfoRow) -> ContactInfo:
    return ContactInfo(
        id=r.id,
        organization_name=r.organization_name,
        address=r.address,
        phone=r.phone,
        email=r.email,
        schedule=r.schedule,
        map_url=r.map_url,
    )


class SqlContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _row(self) -> ContactInfoRow | None:
        return (await self._s.execute(select(ContactInfoRow).limit(1))).scalar_one_or_none()

    async def get(self) -> ContactInfo | None:
        row = await self._row()
        return to_domain(row) if row else None

    async def upsert(self, changes: dict[str, object]) -> ContactInfo:
        row = await self._row()
        if row is None:
            row = ContactInfoRow(organization_name=DEFAULT_ORGANIZATION)
            self._s.add(row)
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)
