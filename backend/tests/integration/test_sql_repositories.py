from uuid import uuid4

import pytest

from app.features.clinical_content.domain.model import ClinicalDraft, ContentKind
from app.features.clinical_content.infrastructure.repository import SqlClinicalContentRepository
from app.features.diseases.infrastructure.repository import SqlDiseaseRepository
from app.features.documents.domain.model import NewDocument
from app.features.documents.infrastructure.repository import SqlDocumentRepository
from app.features.publications.domain.model import NewPublication
from app.features.publications.infrastructure.repository import SqlPublicationRepository
from app.features.users.domain.model import NewUser, UserChanges
from app.features.users.infrastructure.repository import SqlUserRepository
from app.shared.domain.actor import Role, Section

pytestmark = pytest.mark.integration


async def author(session):
    return await SqlUserRepository(session).add(
        NewUser(email="enc@holh.cu", full_name="Encargada", role=Role.MEDICO, password_hash="x")
    )


async def test_users_email_lookup_is_case_insensitive_and_deactivation_persists(session):
    repo = SqlUserRepository(session)
    user = await author(session)
    assert (await repo.get_by_email("ENC@HOLH.CU")).id == user.id
    await repo.update(user.id, UserChanges(is_active=False))
    assert (await repo.get(user.id)).is_active is False


async def test_user_permissions_are_replaced_and_admins_counted(session):
    repo = SqlUserRepository(session)
    user = await repo.add(
        NewUser(
            email="m@holh.cu",
            full_name="Médica",
            role=Role.MEDICO,
            password_hash="x",
            permissions=frozenset({Section.GUIAS, Section.DOCUMENTOS}),
        )
    )
    assert user.permissions == {Section.GUIAS, Section.DOCUMENTOS}
    updated = await repo.update(user.id, UserChanges(permissions=frozenset({Section.ENLACES})))
    assert updated.permissions == {Section.ENLACES}
    assert (await repo.get(user.id)).permissions == {Section.ENLACES}
    assert await repo.count_active_admins() == 0
    await repo.update(user.id, UserChanges(role=Role.ADMINISTRADOR, permissions=frozenset()))
    assert await repo.count_active_admins() == 1


async def test_publications_search_update_image_key_and_author(session):
    repo, user = SqlPublicationRepository(session), await author(session)
    old = await repo.add(NewPublication("Jornada científica", "https://holh.sld.cu/jornada", None, user.id))
    new = await repo.add(
        NewPublication("Guía OMS", "https://who.int/guia", "Recomendaciones", user.id, image_key="a" * 32 + ".png")
    )
    assert {p.id for p in await repo.list(None)} == {new.id, old.id}
    assert [p.title for p in await repo.list("JORNADA")] == ["Jornada científica"]
    assert [p.title for p in await repo.list("who.int")] == ["Guía OMS"]
    assert new.author_name == "Encargada" and new.has_image and new.domain == "who.int"
    updated = await repo.update(new.id, {"title": "Guía OMS 2026", "image_key": None})
    assert updated.title == "Guía OMS 2026" and not updated.has_image
    assert await repo.delete(old.id) and not await repo.delete(old.id)


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


async def test_helpline_config_singleton_and_professional_slots_roundtrip(session):
    from dataclasses import replace
    from datetime import time

    from app.features.helpline.domain.model import DEFAULT_CONFIG, TimeSlot
    from app.features.helpline.infrastructure.repository import SqlHelplineRepository

    repo = SqlHelplineRepository(session)
    assert await repo.get_config() is None
    await repo.save_config(DEFAULT_CONFIG)
    saved = await repo.save_config(replace(DEFAULT_CONFIG, phone="+53 7 649 0000"))
    assert saved.phone == "+53 7 649 0000" and saved.slots == DEFAULT_CONFIG.slots
    slot = TimeSlot(2, time(9), time(15, 30))
    pro = await repo.add_professional(
        {
            "full_name": "Dra. Ana",
            "specialty": "Pediatría",
            "phone": "+53 5 1",
            "sort_order": 0,
            "is_active": True,
            "slots": [slot],
        }
    )
    assert pro.slots == [slot]
    updated = await repo.update_professional(pro.id, {"is_active": False, "slots": []})
    assert updated.slots == [] and not updated.is_active
    assert await repo.list_professionals(active_only=True) == []
    assert await repo.delete_professional(pro.id)
