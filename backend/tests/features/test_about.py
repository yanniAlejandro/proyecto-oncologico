from uuid import uuid4

import pytest

from app.features.about.application import use_cases as uc
from app.features.about.domain.model import slugify
from app.scripts.about_drafts import DRAFTS
from app.shared.domain.actor import Actor, Role, Section
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, EDITOR, PNG, FakeAbout, FakeStorage
from tests.helpers import err, ok


@pytest.fixture
def world(tmp_path):
    return FakeAbout(), FakeStorage(tmp_path)


def test_slugify_for_the_index_anchors():
    assert slugify("Derechos del paciente y su familia") == "derechos-del-paciente-y-su-familia"
    assert slugify("Oncología pediátrica ") == "oncologia-pediatrica"
    assert slugify("¡¿!") == "apartado"


def test_drafts_cover_the_six_agreed_sections_and_are_marked_pending():
    titles = [t for t, _ in DRAFTS]
    assert len(titles) == 6 and titles[0] == "El Centro de Oncología y Radiobiología"
    assert any("pediátrica" in t for t in titles) and any("Derechos" in t for t in titles)
    assert any("Horarios de visita" in t for t in titles)
    assert all(body.startswith("> Borrador pendiente de validar") for _, body in DRAFTS)


async def test_create_appends_with_unique_slug_and_requires_permission(world):
    repo, storage = world
    create = uc.CreateAboutSection(repo, storage)
    first = ok(await create(EDITOR, title="Quiénes somos", body="Texto"))
    second = ok(await create(ADMIN, title="Quiénes somos", body="Otro"))
    assert (first.slug, second.slug) == ("quienes-somos", "quienes-somos-2")
    assert second.sort_order > first.sort_order
    err(await create(DOCTOR, title="Nuevo", body="Texto"), ErrorKind.FORBIDDEN)
    err(await create(None, title="Nuevo", body="Texto"), ErrorKind.UNAUTHENTICATED)
    only_pubs = Actor(id=uuid4(), role=Role.MEDICO, permissions=frozenset({Section.PUBLICACIONES}))
    err(await create(only_pubs, title="Nuevo", body="Texto"), ErrorKind.FORBIDDEN)
    err(await create(EDITOR, title="ab", body="Texto"), ErrorKind.INVALID)
    err(await create(EDITOR, title="Título", body="   "), ErrorKind.INVALID)


async def test_list_is_public_and_ordered(world):
    repo, storage = world
    create = uc.CreateAboutSection(repo, storage)
    await create(EDITOR, title="Segundo", body="b", sort_order=20)
    await create(EDITOR, title="Primero", body="a", sort_order=10)
    assert [s.title for s in await uc.ListAboutSections(repo)()] == ["Primero", "Segundo"]


async def test_update_text_order_and_photo_lifecycle(world):
    repo, storage = world
    section = ok(await uc.CreateAboutSection(repo, storage)(EDITOR, title="Sala", body="Texto", image=PNG))
    first_key = section.image_key
    assert storage.files[first_key] == PNG

    update = uc.UpdateAboutSection(repo, storage)
    renamed = ok(await update(EDITOR, section.id, {"title": "La sala pediátrica", "sort_order": 5}))
    assert renamed.slug == "la-sala-pediatrica" and renamed.sort_order == 5 and renamed.image_key == first_key

    replaced = ok(await update(EDITOR, section.id, {}, image=PNG))
    assert replaced.image_key != first_key and first_key not in storage.files

    removed = ok(await update(EDITOR, section.id, {}, remove_image=True))
    assert not removed.has_image and storage.files == {}

    err(await update(EDITOR, section.id, {}, image=b"<svg/>"), ErrorKind.INVALID)
    err(await update(DOCTOR, section.id, {"title": "No"}), ErrorKind.FORBIDDEN)
    err(await update(EDITOR, uuid4(), {"title": "Nadie"}), ErrorKind.NOT_FOUND)


async def test_delete_removes_photo_and_image_is_served(world):
    repo, storage = world
    section = ok(await uc.CreateAboutSection(repo, storage)(EDITOR, title="Con foto", body="x", image=PNG))
    served = ok(await uc.GetAboutImage(repo, storage)(section.id))
    assert served.media_type == "image/png"
    ok(await uc.DeleteAboutSection(repo, storage)(EDITOR, section.id))
    assert storage.files == {} and repo.rows == {}
    err(await uc.GetAboutImage(repo, storage)(section.id), ErrorKind.NOT_FOUND)
