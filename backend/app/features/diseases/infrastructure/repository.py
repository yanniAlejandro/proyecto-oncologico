from uuid import UUID

from sqlalchemy import delete, func, or_, select
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

    async def update(self, disease_id: UUID, changes: dict[str, object]) -> Disease | None:
        row = await self._s.get(DiseaseRow, disease_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)

    async def usage(self, disease_id: UUID) -> int:
        from app.features.clinical_content.infrastructure.orm import DiagnosticGuideRow, TreatmentProtocolRow

        total = 0
        for model in (DiagnosticGuideRow, TreatmentProtocolRow):
            q = select(func.count()).select_from(model).where(model.disease_id == disease_id)
            total += int((await self._s.execute(q)).scalar_one())
        return total

    async def delete(self, disease_id: UUID) -> bool:
        result = await self._s.execute(delete(DiseaseRow).where(DiseaseRow.id == disease_id))
        await self._s.commit()
        return bool(result.rowcount)

    async def add(self, name: str, description: str | None) -> Disease:
        row = DiseaseRow(name=name, description=description)
        self._s.add(row)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)
