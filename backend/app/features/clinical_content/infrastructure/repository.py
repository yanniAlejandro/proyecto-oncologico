from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.clinical_content.domain.model import ClinicalDoc, ClinicalDraft, ContentKind
from app.features.clinical_content.infrastructure.orm import DiagnosticGuideRow, TreatmentProtocolRow
from app.features.diseases.infrastructure.orm import DiseaseRow

ROW_BY_KIND = {ContentKind.GUIDE: DiagnosticGuideRow, ContentKind.PROTOCOL: TreatmentProtocolRow}


def to_domain(row: DiagnosticGuideRow | TreatmentProtocolRow) -> ClinicalDoc:
    return ClinicalDoc(
        id=row.id,
        disease_id=row.disease_id,
        disease_name=row.disease.name,
        title=row.title,
        content=row.content,
        created_at=row.created_at,
        updated_at=row.updated_at,
        author_name=row.author.full_name if row.author else None,
    )


class SqlClinicalContentRepository:
    def __init__(self, session: AsyncSession, kind: ContentKind) -> None:
        self._s = session
        self._row = ROW_BY_KIND[kind]

    async def list(self, search: str | None) -> list[ClinicalDoc]:
        Row = self._row
        q = select(Row).order_by(Row.title)
        if search:
            p = f"%{search}%"
            # Subconsulta para no chocar con el JOIN implícito de lazy="joined".
            matching_diseases = select(DiseaseRow.id).where(DiseaseRow.name.ilike(p))
            q = q.where(or_(Row.title.ilike(p), Row.content.ilike(p), Row.disease_id.in_(matching_diseases)))
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().unique().all()]

    async def get(self, doc_id: UUID) -> ClinicalDoc | None:
        row = (await self._s.execute(select(self._row).where(self._row.id == doc_id))).scalar_one_or_none()
        return to_domain(row) if row else None

    async def add(self, draft: ClinicalDraft, author_id: UUID) -> ClinicalDoc:
        row = self._row(disease_id=draft.disease_id, title=draft.title, content=draft.content, created_by=author_id)
        self._s.add(row)
        await self._s.commit()
        return await self._reload(row.id)

    async def update(self, doc_id: UUID, changes: dict[str, object]) -> ClinicalDoc | None:
        row = await self._s.get(self._row, doc_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._s.commit()
        return await self._reload(doc_id)

    async def delete(self, doc_id: UUID) -> bool:
        row = await self._s.get(self._row, doc_id)
        if row is None:
            return False
        await self._s.delete(row)
        await self._s.commit()
        return True

    async def _reload(self, doc_id: UUID) -> ClinicalDoc:
        self._s.expire_all()
        doc = await self.get(doc_id)
        assert doc is not None
        return doc
