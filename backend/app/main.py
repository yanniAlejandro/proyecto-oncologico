from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.auth.presentation.router import router as auth_router
from app.features.clinical_content.presentation.router import guides_router, protocols_router
from app.features.contact.presentation.router import router as contact_router
from app.features.diseases.presentation.router import router as diseases_router
from app.features.documents.presentation.router import router as documents_router
from app.features.interest_links.presentation.router import router as links_router
from app.features.news.presentation.router import router as news_router
from app.features.users.presentation.router import router as users_router
from app.shared.infrastructure import orm_registry  # noqa: F401  (registra todos los mapeos ORM)
from app.shared.infrastructure.config import settings


def build_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(auth_router, prefix="/auth", tags=["auth"])
    api.include_router(users_router, prefix="/users", tags=["users"])
    api.include_router(news_router, prefix="/news", tags=["news"])
    api.include_router(diseases_router, prefix="/diseases", tags=["diseases"])
    api.include_router(guides_router, prefix="/diagnostic-guides", tags=["diagnostic-guides"])
    api.include_router(protocols_router, prefix="/treatment-protocols", tags=["treatment-protocols"])
    api.include_router(documents_router, prefix="/documents", tags=["documents"])
    api.include_router(links_router, prefix="/interest-links", tags=["interest-links"])
    api.include_router(contact_router, prefix="/contact", tags=["contact"])
    return api


def create_app() -> FastAPI:
    app = FastAPI(title="Portal Oncológico API", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_api_router(), prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
