from app.features.diseases.application.use_cases import CreateDisease, ListDiseases
from app.shared.domain.result import ErrorKind
from tests.fakes import DOCTOR, EDITOR, FakeDiseases
from tests.helpers import err, ok


async def test_diseases_are_unique_case_insensitive():
    repo = FakeDiseases("Melanoma")
    err(await CreateDisease(repo)(EDITOR, "  melanoma "), ErrorKind.CONFLICT)
    err(await CreateDisease(repo)(DOCTOR, "Linfoma"), ErrorKind.FORBIDDEN)
    created = ok(await CreateDisease(repo)(EDITOR, " Linfoma ", "desc"))
    assert created.name == "Linfoma"
    assert [d.name for d in await ListDiseases(repo)("lin")] == ["Linfoma"]


async def test_update_and_delete_diseases():
    from uuid import uuid4

    from app.features.diseases.application.use_cases import DeleteDisease, UpdateDisease

    repo = FakeDiseases("Melanoma", "Linfoma")
    melanoma, linfoma = repo.by_name("Melanoma"), repo.by_name("Linfoma")
    updated = ok(await UpdateDisease(repo)(EDITOR, melanoma.id, name=" Melanoma maligno ", description=" "))
    assert updated.name == "Melanoma maligno" and updated.description is None
    err(await UpdateDisease(repo)(EDITOR, melanoma.id, name="linfoma"), ErrorKind.CONFLICT)
    err(await UpdateDisease(repo)(DOCTOR, melanoma.id, name="X y"), ErrorKind.FORBIDDEN)
    err(await UpdateDisease(repo)(EDITOR, uuid4(), name="Nada"), ErrorKind.NOT_FOUND)

    repo.in_use[linfoma.id] = 2
    msg = err(await DeleteDisease(repo)(EDITOR, linfoma.id), ErrorKind.CONFLICT)
    assert "2 guías o protocolos" in msg
    ok(await DeleteDisease(repo)(EDITOR, melanoma.id))
    err(await DeleteDisease(repo)(EDITOR, melanoma.id), ErrorKind.NOT_FOUND)
