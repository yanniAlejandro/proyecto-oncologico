from uuid import uuid4

import pytest

from app.features.publications.application import use_cases as uc
from app.features.publications.domain.model import LinkPreview
from app.features.publications.domain.open_graph import parse_open_graph
from app.shared.domain.actor import Actor, Role, Section
from app.shared.domain.image_policy import sniff_image, validate_image
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, EDITOR, PNG, FakePreviewer, FakePublications, FakeStorage
from tests.helpers import err, ok

URL = "https://www.who.int/es/news/item/cancer"
OG_IMAGE = "https://cdn.who.int/cancer.png"


@pytest.fixture
def world(tmp_path):
    previewer = FakePreviewer(
        pages={URL: LinkPreview(url=URL, title="Día mundial contra el cáncer", image_url=OG_IMAGE)},
        images={OG_IMAGE: PNG},
    )
    return FakePublications(), FakeStorage(tmp_path), previewer


def create(world):
    repo, storage, previewer = world
    return uc.CreatePublication(repo, storage, previewer)


# --- dominio puro ---------------------------------------------------------------


def test_open_graph_like_whatsapp():
    html = """<html><head><title>Ignorado</title>
      <meta property="og:title" content="Día &amp; noche">
      <meta property="og:description" content="  Texto   con  espacios ">
      <meta property="og:image" content="/img/portada.jpg">
      <meta property="og:site_name" content="OMS"></head></html>"""
    p = parse_open_graph(html, "https://who.int/es/nota")
    assert p.title == "Día & noche"
    assert p.description == "Texto con espacios"
    assert p.image_url == "https://who.int/img/portada.jpg"  # relativa → absoluta
    assert p.site_name == "OMS"


def test_open_graph_falls_back_to_title_and_meta_description():
    html = '<title> Portal  HOLH </title><meta name="description" content="Resumen">'
    p = parse_open_graph(html, "https://holh.sld.cu")
    assert (p.title, p.description, p.image_url) == ("Portal HOLH", "Resumen", None)


def test_open_graph_ignores_non_http_images_and_broken_html():
    p = parse_open_graph('<meta property="og:image" content="javascript:alert(1)"><div', "https://x.cu")
    assert p.image_url is None and p.is_empty


@pytest.mark.parametrize(
    ("data", "ext"),
    [
        (PNG, ".png"),
        (b"\xff\xd8\xff\xe0" + b"0" * 10, ".jpg"),
        (b"GIF89a" + b"0" * 10, ".gif"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", ".webp"),
        (b"<svg onload=alert(1)>", None),
        (b"%PDF-1.4", None),
    ],
)
def test_images_are_identified_by_content(data, ext):
    assert sniff_image(data) == ext


def test_validate_image_limits():
    err(validate_image(b""), ErrorKind.INVALID)
    err(validate_image(PNG, max_bytes=10), ErrorKind.TOO_LARGE)
    assert validate_image(PNG).value == ".png"


# --- casos de uso -------------------------------------------------------------------


async def test_preview_requires_permission_and_valid_url(world):
    _, _, previewer = world
    preview = uc.PreviewLink(previewer)
    assert ok(await preview(EDITOR, URL)).title == "Día mundial contra el cáncer"
    assert ok(await preview(EDITOR, "https://sin-og.cu")) is None  # → el formulario pasa a modo manual
    err(await preview(EDITOR, "ftp://x.cu"), ErrorKind.INVALID)
    err(await preview(DOCTOR, URL), ErrorKind.FORBIDDEN)
    err(await preview(None, URL), ErrorKind.UNAUTHENTICATED)


async def test_create_downloads_og_image_into_our_storage(world):
    repo, storage, previewer = world
    pub = ok(
        await create(world)(
            EDITOR, title=" Día mundial ", url=URL, description="  ", image=uc.ImageSource(url=OG_IMAGE)
        )
    )
    assert pub.title == "Día mundial" and pub.description is None
    assert pub.image_key and storage.files[pub.image_key] == PNG  # copia local, no hotlink
    assert previewer.fetched == [OG_IMAGE]


async def test_manual_upload_has_priority_and_is_validated(world):
    repo, storage, previewer = world
    pub = ok(await create(world)(EDITOR, title="Manual", url=URL, image=uc.ImageSource(upload=PNG, url=OG_IMAGE)))
    assert previewer.fetched == [] and storage.files[pub.image_key] == PNG
    err(
        await create(world)(EDITOR, title="Manual", url=URL, image=uc.ImageSource(upload=b"<svg/>")),
        ErrorKind.INVALID,
    )
    assert len(repo.rows) == 1


async def test_unreachable_og_image_does_not_block_publishing(world):
    repo, storage, _ = world
    pub = ok(
        await create(world)(EDITOR, title="Sin imagen", url=URL, image=uc.ImageSource(url="https://caida.cu/i.png"))
    )
    assert not pub.has_image and storage.files == {}


async def test_create_validates_and_requires_permission(world):
    err(await create(world)(EDITOR, title="ab", url=URL), ErrorKind.INVALID)
    err(await create(world)(EDITOR, title="Título", url="javascript:alert(1)"), ErrorKind.INVALID)
    err(await create(world)(DOCTOR, title="Título", url=URL), ErrorKind.FORBIDDEN)
    only_docs = Actor(id=uuid4(), role=Role.MEDICO, permissions=frozenset({Section.DOCUMENTOS}))
    err(await create(world)(only_docs, title="Título", url=URL), ErrorKind.FORBIDDEN)
    ok(await create(world)(ADMIN, title="Título", url=URL))


async def test_db_failure_removes_downloaded_image(world):
    repo, storage, previewer = world

    async def boom(new):
        raise RuntimeError("BD caída")

    repo.add = boom
    with pytest.raises(RuntimeError):
        await create(world)(EDITOR, title="Título", url=URL, image=uc.ImageSource(url=OG_IMAGE))
    assert storage.files == {}


async def test_update_replaces_and_removes_image_and_cleans_old_file(world):
    repo, storage, previewer = world
    pub = ok(await create(world)(EDITOR, title="Original", url=URL, image=uc.ImageSource(url=OG_IMAGE)))
    update = uc.UpdatePublication(repo, storage, previewer)
    other = Actor(id=uuid4(), role=Role.MEDICO, permissions=frozenset({Section.PUBLICACIONES}))

    replaced = ok(await update(other, pub.id, {"title": "Editada por otro"}, image=uc.ImageSource(upload=PNG)))
    assert replaced.title == "Editada por otro"  # CRUD sobre lo de otros
    assert replaced.image_key != pub.image_key and pub.image_key not in storage.files

    kept = ok(await update(EDITOR, pub.id, {"description": "Nueva"}))
    assert kept.image_key == replaced.image_key and kept.description == "Nueva"

    removed = ok(await update(EDITOR, pub.id, {}, remove_image=True))
    assert not removed.has_image and storage.files == {}

    err(await update(EDITOR, pub.id, {"url": "nope"}), ErrorKind.INVALID)
    err(await update(EDITOR, uuid4(), {"title": "Nadie"}), ErrorKind.NOT_FOUND)
    err(await update(DOCTOR, pub.id, {"title": "No"}), ErrorKind.FORBIDDEN)


async def test_delete_removes_row_and_image(world):
    repo, storage, previewer = world
    pub = ok(await create(world)(EDITOR, title="Borrar", url=URL, image=uc.ImageSource(url=OG_IMAGE)))
    err(await uc.DeletePublication(repo, storage)(DOCTOR, pub.id), ErrorKind.FORBIDDEN)
    ok(await uc.DeletePublication(repo, storage)(EDITOR, pub.id))
    assert repo.rows == {} and storage.files == {}
    err(await uc.DeletePublication(repo, storage)(EDITOR, pub.id), ErrorKind.NOT_FOUND)


async def test_list_is_public_and_searchable(world):
    repo, _, _ = world
    await create(world)(EDITOR, title="Jornada de pediatría", url="https://holh.sld.cu/j")
    await create(world)(EDITOR, title="Guía OMS", url=URL, description="cáncer infantil")
    assert len(await uc.ListPublications(repo)()) == 2
    assert [p.title for p in await uc.ListPublications(repo)(" INFANTIL ")] == ["Guía OMS"]
    assert [p.title for p in await uc.ListPublications(repo)("holh.sld")] == ["Jornada de pediatría"]


async def test_image_served_only_if_stored(world):
    repo, storage, _ = world
    pub = ok(await create(world)(EDITOR, title="Con imagen", url=URL, image=uc.ImageSource(url=OG_IMAGE)))
    served = ok(await uc.GetPublicationImage(repo, storage)(pub.id))
    assert served.media_type == "image/png" and served.path.read_bytes() == PNG
    bare = ok(await create(world)(EDITOR, title="Sin imagen", url=URL))
    err(await uc.GetPublicationImage(repo, storage)(bare.id), ErrorKind.NOT_FOUND)
