"""Importa todos los modelos ORM para que ``Base.metadata`` esté completo (Alembic, seeds)."""

from app.features.clinical_content.infrastructure.orm import DiagnosticGuideRow, TreatmentProtocolRow
from app.features.contact.infrastructure.orm import ContactInfoRow
from app.features.diseases.infrastructure.orm import DiseaseRow
from app.features.documents.infrastructure.orm import DocumentRow
from app.features.interest_links.infrastructure.orm import InterestLinkRow
from app.features.publications.infrastructure.orm import PublicationRow
from app.features.users.infrastructure.orm import UserPermissionRow, UserRow
from app.shared.infrastructure.database import Base

__all__ = [
    "Base",
    "UserRow",
    "UserPermissionRow",
    "DiseaseRow",
    "PublicationRow",
    "DiagnosticGuideRow",
    "TreatmentProtocolRow",
    "DocumentRow",
    "InterestLinkRow",
    "ContactInfoRow",
]
