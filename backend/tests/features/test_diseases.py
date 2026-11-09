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
