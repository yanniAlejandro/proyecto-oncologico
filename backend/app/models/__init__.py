from app.models.contact import ContactInfo
from app.models.diagnostic_guide import DiagnosticGuide
from app.models.disease import Disease
from app.models.document import Document
from app.models.interest_link import InterestLink
from app.models.news import News
from app.models.treatment_protocol import TreatmentProtocol
from app.models.user import User

__all__ = [
    "User",
    "Disease",
    "News",
    "DiagnosticGuide",
    "TreatmentProtocol",
    "Document",
    "InterestLink",
    "ContactInfo",
]
