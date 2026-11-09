import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.features.diseases.infrastructure.orm import DiseaseRow
from app.features.users.infrastructure.orm import UserRow
from app.shared.infrastructure.database import Base


class _ClinicalColumns:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diseases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @declared_attr
    def disease(cls) -> Mapped[DiseaseRow]:
        return relationship(DiseaseRow, lazy="joined")

    @declared_attr
    def author(cls) -> Mapped[UserRow | None]:
        return relationship(UserRow, lazy="joined")


class DiagnosticGuideRow(_ClinicalColumns, Base):
    __tablename__ = "diagnostic_guides"


class TreatmentProtocolRow(_ClinicalColumns, Base):
    __tablename__ = "treatment_protocols"


ClinicalRow = DiagnosticGuideRow | TreatmentProtocolRow
