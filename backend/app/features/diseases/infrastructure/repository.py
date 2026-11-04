from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.diseases.domain.model import Disease
from app.features.diseases.infrastructure.orm import DiseaseRow


def to_domain(row: DiseaseRow) -> Disease:
    return Disease(id=row.id, name=row.name, description=row.description)


class SqlDiseaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list(self, search: str | None = None) -> list[Disease]:
        q = select(DiseaseRow).order_by(DiseaseRow.name)
        if search:
            p = f"%{search}%"
            q = q.where(or_(DiseaseRow.name.ilike(p), DiseaseRow.description.ilike(p)))
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get(self, disease_id: UUID) -> Disease | None:
        row = await self._s.get(DiseaseRow, disease_id)
        return to_domain(row) if row else None

    async def get_by_name(self, name: str) -> Disease | None:
        q = select(DiseaseRow).where(func.lower(DiseaseRow.name) == name.lower())
        row = (await self._s.execute(q)).scalar_one_or_none()
        return to_domain(row) if row else None

    async def add(self, name: str, description: str | None) -> Disease:
        row = DiseaseRow(name=name, description=description)
        self._s.add(row)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)
