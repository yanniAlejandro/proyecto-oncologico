from uuid import uuid4

from app.features.contact.application.use_cases import GetContact, UpdateContact
from app.features.interest_links.application import use_cases as uc
from app.shared.domain.result import ErrorKind
from tests.fakes import ADMIN, DOCTOR, EDITOR, FakeContact, FakeLinks
from tests.helpers import err, ok


async def test_links_public_list_only_active_sorted():
    repo = FakeLinks()
    ok(await uc.CreateLink(repo)(EDITOR, {"title": "B", "url": "https://b.cu", "sort_order": 2}))
    ok(await uc.CreateLink(repo)(EDITOR, {"title": "A", "url": "https://a.cu", "sort_order": 1}))
    ok(await uc.CreateLink(repo)(EDITOR, {"title": "Oculto", "url": "https://c.cu", "is_active": False}))
    assert [link.title for link in await uc.ListActiveLinks(repo)()] == ["A", "B"]


async def test_links_validation_and_roles():
    repo = FakeLinks()
    err(await uc.CreateLink(repo)(EDITOR, {"title": "x", "url": "ftp://x"}), ErrorKind.INVALID)
    err(await uc.CreateLink(repo)(DOCTOR, {"title": "x", "url": "https://x.cu"}), ErrorKind.FORBIDDEN)
    link = ok(await uc.CreateLink(repo)(ADMIN, {"title": "x", "url": "https://x.cu"}))
    err(await uc.UpdateLink(repo)(EDITOR, link.id, {"url": "nada"}), ErrorKind.INVALID)
    assert ok(await uc.UpdateLink(repo)(EDITOR, link.id, {"title": "y"})).title == "y"
    err(await uc.UpdateLink(repo)(EDITOR, uuid4(), {"title": "y"}), ErrorKind.NOT_FOUND)
    ok(await uc.DeleteLink(repo)(EDITOR, link.id))
    err(await uc.DeleteLink(repo)(EDITOR, link.id), ErrorKind.NOT_FOUND)


async def test_contact_public_read_admin_only_write():
    repo = FakeContact()
    err(await GetContact(repo)(), ErrorKind.NOT_FOUND)
    err(await UpdateContact(repo)(EDITOR, {"phone": "1"}), ErrorKind.FORBIDDEN)
    info = ok(await UpdateContact(repo)(ADMIN, {"phone": "+53 7 000", "id": "ignorado"}))
    assert info.phone == "+53 7 000" and info.organization_name == "Hospital Oncológico de La Habana"
    assert ok(await GetContact(repo)()).phone == "+53 7 000"
