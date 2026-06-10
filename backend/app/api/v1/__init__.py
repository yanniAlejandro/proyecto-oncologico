from fastapi import APIRouter

from app.api.v1 import (
    auth,
    contact,
    diagnostic_guides,
    diseases,
    documents,
    interest_links,
    news,
    treatment_protocols,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(diseases.router, prefix="/diseases", tags=["diseases"])
api_router.include_router(diagnostic_guides.router, prefix="/diagnostic-guides", tags=["diagnostic-guides"])
api_router.include_router(treatment_protocols.router, prefix="/treatment-protocols", tags=["treatment-protocols"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(interest_links.router, prefix="/interest-links", tags=["interest-links"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
