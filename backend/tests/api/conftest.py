"""App real con los adaptadores sustituidos por fakes vía ``dependency_overrides``."""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.features.auth.presentation.deps import get_token_service
from app.features.clinical_content.presentation.router import GUIDE_REPOSITORY, PROTOCOL_REPOSITORY
from app.features.contact.presentation.router import get_contact_repository
from app.features.diseases.presentation.deps import get_disease_repository
from app.features.documents.presentation.router import (
    get_document_repository,
    get_file_storage,
    get_max_upload_bytes,
)
from app.features.interest_links.presentation.router import get_link_repository
from app.features.news.presentation.router import get_news_repository
from app.features.users.presentation.deps import get_password_hasher, get_user_repository
from app.main import create_app
from tests.fakes import (
    ADMIN,
    DOCTOR,
    MANAGER,
    FakeClinical,
    FakeContact,
    FakeDiseases,
    FakeDocuments,
    FakeHasher,
    FakeLinks,
    FakeNews,
    FakeStorage,
    FakeTokens,
    FakeUsers,
)

MAX_UPLOAD = 1024


@dataclass
class World:
    client: TestClient
    users: FakeUsers
    diseases: FakeDiseases
    guides: FakeClinical
    protocols: FakeClinical
    news: FakeNews
    documents: FakeDocuments
    storage: FakeStorage

    def as_(self, who: str | None) -> dict[str, str]:
        actor = {"admin": ADMIN, "encargado": MANAGER, "medico": DOCTOR}.get(who or "")
        return {"Authorization": f"Bearer token:{actor.id}"} if actor else {}


@pytest.fixture
def world(tmp_path) -> World:
    app = create_app()
    users = FakeUsers.with_actors(ADMIN, MANAGER, DOCTOR)
    diseases = FakeDiseases("Cáncer de mama", "Leucemia")
    w = World(
        client=TestClient(app),
        users=users,
        diseases=diseases,
        guides=FakeClinical(diseases),
        protocols=FakeClinical(diseases),
        news=FakeNews(),
        documents=FakeDocuments(),
        storage=FakeStorage(tmp_path),
    )
    links, contact = FakeLinks(), FakeContact()
    app.dependency_overrides.update(
        {
            get_user_repository: lambda: w.users,
            get_password_hasher: FakeHasher,
            get_token_service: FakeTokens,
            get_disease_repository: lambda: w.diseases,
            GUIDE_REPOSITORY: lambda: w.guides,
            PROTOCOL_REPOSITORY: lambda: w.protocols,
            get_news_repository: lambda: w.news,
            get_document_repository: lambda: w.documents,
            get_file_storage: lambda: w.storage,
            get_max_upload_bytes: lambda: MAX_UPLOAD,
            get_link_repository: lambda: links,
            get_contact_repository: lambda: contact,
        }
    )
    return w
