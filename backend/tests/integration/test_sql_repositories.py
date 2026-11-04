from uuid import uuid4

import pytest

from app.features.clinical_content.domain.model import ClinicalDraft, ContentKind
from app.features.clinical_content.infrastructure.repository import SqlClinicalContentRepository
from app.features.diseases.infrastructure.repository import SqlDiseaseRepository
from app.features.documents.domain.model import NewDocument
from app.features.documents.infrastructure.repository import SqlDocumentRepository
from app.features.news.domain.model import NewsDraft
from app.features.news.infrastructure.repository import SqlNewsRepository
from app.features.users.domain.model import NewUser
from app.features.users.infrastructure.repository import SqlUserRepository
from app.shared.domain.actor import Role

pytestmark = pytest.mark.integration


async def author(session):
    return await SqlUserRepository(session).add(
        NewUser(email="enc@holh.cu", full_name="Encargada", role=Role.ENCARGADO, password_hash="x")
    )


async def test_users_email_lookup_is_case_insensitive_and_deactivation_persists(session):
    repo = SqlUserRepository(session)
    user = await author(session)
    assert (await repo.get_by_email("ENC@HOLH.CU")).id == user.id
    await repo.set_active(user.id, False)
    assert (await repo.get(user.id)).is_active is False


async def test_news_published_filter_search_and_author_name(session):
    repo, user = SqlNewsRepository(session), await author(session)
    pub = await repo.add(NewsDraft("Jornada científica", "contenido de la jornada"), user.id)
    await repo.add(NewsDraft("Borrador", "texto interno", is_published=False), user.id)
    assert [n.id for n in await repo.list(published_only=True, search=None)] == [pub.id]
    assert len(await repo.list(published_only=False, search=None)) == 2
    assert [n.title for n in await repo.list(published_only=True, search="JORNADA")] == ["Jornada científica"]
    assert pub.author_name == "Encargada"
    updated = await repo.update(pub.id, {"title": "Jornada 2026"})
    assert updated.title == "Jornada 2026" and updated.updated_at >= pub.updated_at
    assert await repo.delete(pub.id) and not await repo.delete(pub.id)


@pytest.mark.parametrize("kind", list(ContentKind))
async def test_clinical_search_by_title_content_or_disease(session, kind):
    user = await author(session)
    diseases = SqlDiseaseRepository(session)
    mama, leuc = await diseases.add("Cáncer de mama", None), await diseases.add("Leucemia", None)
    repo = SqlClinicalContentRepository(session, kind)
    a = await repo.add(ClinicalDraft(mama.id, "Estadificación", "TNM"), user.id)
    await repo.add(ClinicalDraft(leuc.id, "Inducción", "quimioterapia intensiva"), user.id)
    assert [d.id for d in await repo.list("mama")] == [a.id]  # por nombre de enfermedad
    assert [d.title for d in await repo.list("intensiva")] == ["Inducción"]  # por contenido
    assert len(await repo.list(None)) == 2
    moved = await repo.update(a.id, {"disease_id": leuc.id})
    assert moved.disease_name == "Leucemia" and moved.author_name == "Encargada"


async def test_documents_roundtrip_with_storage_fields(session):
    repo, user = SqlDocumentRepository(session), await author(session)
    doc = await repo.add(
        NewDocument(
            title="Informe",
            description=None,
            file_name="i.pdf",
            file_type="PDF",
            uploaded_by=user.id,
            storage_key=f"{uuid4().hex}.pdf",
            size_bytes=10,
        )
    )
    assert doc.has_stored_file and doc.is_previewable and doc.uploader_name == "Encargada"
    link = await repo.add(
        NewDocument(
            title="OMS",
            description="guía",
            file_name="m.pdf",
            file_type="PDF",
            uploaded_by=user.id,
            file_url="https://who.int/m.pdf",
        )
    )
    assert not link.has_stored_file
    assert {d.id for d in await repo.list("guía")} == {link.id}
    assert await repo.delete(doc.id) and await repo.get(doc.id) is None
