from app.features.diseases.application.use_cases import CreateDisease, ListDiseases
from app.features.news.application import use_cases as uc
from app.features.news.domain.model import NewsDraft
from app.shared.domain.result import ErrorKind
from tests.fakes import DOCTOR, MANAGER, FakeDiseases, FakeNews
from tests.helpers import err, ok


async def seed(repo: FakeNews):
    published = ok(await uc.CreateNews(repo)(MANAGER, NewsDraft("Pública", "contenido largo de la noticia")))
    draft = ok(await uc.CreateNews(repo)(MANAGER, NewsDraft("Borrador", "contenido del borrador", is_published=False)))
    return published, draft


async def test_public_listing_hides_drafts_but_managers_see_them():
    repo = FakeNews()
    published, draft = await seed(repo)
    assert [n.id for n in await uc.ListPublishedNews(repo)()] == [published.id]
    assert {n.id for n in ok(await uc.ListAllNews(repo)(MANAGER))} == {published.id, draft.id}
    err(await uc.ListAllNews(repo)(DOCTOR), ErrorKind.FORBIDDEN)
    err(await uc.GetPublishedNews(repo)(draft.id), ErrorKind.NOT_FOUND)


async def test_search_is_trimmed_and_blank_means_all():
    repo = FakeNews()
    await seed(repo)
    assert len(await uc.ListPublishedNews(repo)("   ")) == 1
    assert len(await uc.ListPublishedNews(repo)("  pública ")) == 1
    assert len(await uc.ListPublishedNews(repo)("inexistente")) == 0


async def test_only_managers_write_news():
    repo = FakeNews()
    published, _ = await seed(repo)
    err(await uc.CreateNews(repo)(DOCTOR, NewsDraft("x", "y")), ErrorKind.FORBIDDEN)
    err(await uc.UpdateNews(repo)(None, published.id, {"title": "z"}), ErrorKind.UNAUTHENTICATED)
    err(await uc.DeleteNews(repo)(DOCTOR, published.id), ErrorKind.FORBIDDEN)


async def test_update_ignores_unknown_fields_and_delete_reports_missing():
    repo = FakeNews()
    published, _ = await seed(repo)
    updated = ok(await uc.UpdateNews(repo)(MANAGER, published.id, {"title": "Nuevo", "author_name": "hacker"}))
    assert updated.title == "Nuevo" and updated.author_name != "hacker"
    ok(await uc.DeleteNews(repo)(MANAGER, published.id))
    err(await uc.DeleteNews(repo)(MANAGER, published.id), ErrorKind.NOT_FOUND)


async def test_diseases_are_unique_case_insensitive():
    repo = FakeDiseases("Melanoma")
    err(await CreateDisease(repo)(MANAGER, "  melanoma "), ErrorKind.CONFLICT)
    err(await CreateDisease(repo)(DOCTOR, "Linfoma"), ErrorKind.FORBIDDEN)
    created = ok(await CreateDisease(repo)(MANAGER, " Linfoma ", "desc"))
    assert created.name == "Linfoma"
    assert [d.name for d in await ListDiseases(repo)("lin")] == ["Linfoma"]
