from uuid import uuid4

import pytest

from app.features.clinical_content.application import use_cases as uc
from app.features.clinical_content.domain.model import ClinicalDraft, ContentKind
from app.shared.domain.actor import Actor, Role, Section
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, EDITOR, FakeClinical, FakeDiseases
from tests.helpers import err, ok


@pytest.fixture
def world():
    diseases = FakeDiseases("Cáncer de mama", "Leucemia")
    return diseases, FakeClinical(diseases)


async def create(world, title="Guía de mama", disease="Cáncer de mama"):
    diseases, docs = world
    draft = ClinicalDraft(disease_id=diseases.by_name(disease).id, title=title, content="contenido clínico")
    return ok(await uc.CreateClinicalDoc(ContentKind.GUIDE, docs, diseases)(EDITOR, draft))


async def test_guides_and_protocols_require_a_session(world):
    _, docs = world
    await create(world)
    for kind in ContentKind:
        err(await uc.ListClinicalDocs(kind, docs)(None), ErrorKind.UNAUTHENTICATED)
        assert len(ok(await uc.ListClinicalDocs(kind, docs)(DOCTOR))) == 1


async def test_each_kind_needs_its_own_permission(world):
    diseases, docs = world
    only_guides = Actor(id=uuid4(), role=Role.MEDICO, permissions=frozenset({Section.GUIAS}))
    draft = ClinicalDraft(disease_id=diseases.by_name("Leucemia").id, title="t", content="contenido")
    ok(await uc.CreateClinicalDoc(ContentKind.GUIDE, docs, diseases)(only_guides, draft))
    err(await uc.CreateClinicalDoc(ContentKind.PROTOCOL, docs, diseases)(only_guides, draft), ErrorKind.FORBIDDEN)


async def test_get_respects_read_policy_and_kind_specific_message(world):
    _, docs = world
    doc = await create(world)
    err(await uc.GetClinicalDoc(ContentKind.GUIDE, docs)(None, doc.id), ErrorKind.UNAUTHENTICATED)
    assert ok(await uc.GetClinicalDoc(ContentKind.GUIDE, docs)(DOCTOR, doc.id)).id == doc.id
    assert (
        err(await uc.GetClinicalDoc(ContentKind.GUIDE, docs)(DOCTOR, uuid4()), ErrorKind.NOT_FOUND)
        == "Guía no encontrada"
    )
    msg = err(await uc.GetClinicalDoc(ContentKind.PROTOCOL, docs)(DOCTOR, uuid4()), ErrorKind.NOT_FOUND)
    assert msg == "Protocolo no encontrado"


async def test_doctor_reads_but_cannot_write(world):
    diseases, docs = world
    doc = await create(world)
    draft = ClinicalDraft(disease_id=diseases.by_name("Leucemia").id, title="x", content="y")
    err(await uc.CreateClinicalDoc(ContentKind.GUIDE, docs, diseases)(DOCTOR, draft), ErrorKind.FORBIDDEN)
    err(
        await uc.UpdateClinicalDoc(ContentKind.GUIDE, docs, diseases)(DOCTOR, doc.id, {"title": "z"}),
        ErrorKind.FORBIDDEN,
    )
    err(await uc.DeleteClinicalDoc(ContentKind.GUIDE, docs)(DOCTOR, doc.id), ErrorKind.FORBIDDEN)


async def test_unknown_disease_is_rejected_on_create_and_update(world):
    diseases, docs = world
    doc = await create(world)
    err(
        await uc.CreateClinicalDoc(ContentKind.GUIDE, docs, diseases)(EDITOR, ClinicalDraft(uuid4(), "t", "c")),
        ErrorKind.INVALID,
    )
    err(
        await uc.UpdateClinicalDoc(ContentKind.GUIDE, docs, diseases)(ADMIN, doc.id, {"disease_id": uuid4()}),
        ErrorKind.INVALID,
    )


async def test_update_changes_disease_and_skips_nulls(world):
    diseases, docs = world
    doc = await create(world)
    leucemia = diseases.by_name("Leucemia")
    updated = ok(
        await uc.UpdateClinicalDoc(ContentKind.PROTOCOL, docs, diseases)(
            EDITOR, doc.id, {"disease_id": leucemia.id, "title": None}
        )
    )
    assert updated.disease_name == "Leucemia" and updated.title == doc.title


async def test_search_matches_disease_name(world):
    _, docs = world
    await create(world, "Protocolo A", "Leucemia")
    await create(world, "Protocolo B", "Cáncer de mama")
    found = ok(await uc.ListClinicalDocs(ContentKind.PROTOCOL, docs)(DOCTOR, "leuc"))
    assert [d.title for d in found] == ["Protocolo A"]
