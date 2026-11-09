from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.documents.domain.model import Document, NewDocument
from app.features.documents.infrastructure.orm import DocumentRow


def to_domain(row: DocumentRow) -> Document:
    return Document(
        id=row.id,
        title=row.title,
        description=row.description,
        file_name=row.file_name,
        created_at=row.created_at,
        file_type=row.file_type,
        file_url=row.file_url,
        storage_key=row.storage_key,
        size_bytes=row.size_bytes,
        uploader_name=row.uploader.full_name if row.uploader else None,
    )


class SqlDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list(self, search: str | None) -> list[Document]:
        q = select(DocumentRow).order_by(DocumentRow.created_at.desc())
        if search:
            p = f"%{search}%"
            q = q.where(
                or_(DocumentRow.title.ilike(p), DocumentRow.description.ilike(p), DocumentRow.file_name.ilike(p))
            )
        return [to_domain(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get(self, doc_id: UUID) -> Document | None:
        row = (await self._s.execute(select(DocumentRow).where(DocumentRow.id == doc_id))).scalar_one_or_none()
        return to_domain(row) if row else None

    async def add(self, new: NewDocument) -> Document:
        row = DocumentRow(
            title=new.title,
            description=new.description,
            file_name=new.file_name,
            file_type=new.file_type,
            file_url=new.file_url,
            storage_key=new.storage_key,
            size_bytes=new.size_bytes,
            uploaded_by=new.uploaded_by,
        )
        self._s.add(row)
        await self._s.commit()
        doc_id = row.id  # leer antes de expirar: tras expire_all el acceso dispararía IO síncrono
        self._s.expire_all()
        doc = await self.get(doc_id)
        assert doc is not None
        return doc

    async def delete(self, doc_id: UUID) -> bool:
        row = await self._s.get(DocumentRow, doc_id)
        if row is None:
            return False
        await self._s.delete(row)
        await self._s.commit()
        return True
