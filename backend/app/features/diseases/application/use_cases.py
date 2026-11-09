from app.features.diseases.domain.model import Disease, DiseaseRepository
from app.shared.domain.actor import Actor, Section, require_section
from app.shared.domain.result import AppError, Err, Ok, Result


class ListDiseases:
    def __init__(self, diseases: DiseaseRepository) -> None:
        self._diseases = diseases

    async def __call__(self, search: str | None = None) -> list[Disease]:
        return await self._diseases.list(search.strip() if search else None)


class CreateDisease:
    def __init__(self, diseases: DiseaseRepository) -> None:
        self._diseases = diseases

    async def __call__(self, actor: Actor | None, name: str, description: str | None = None) -> Result[Disease]:
        if isinstance(auth := require_section(actor, Section.ENFERMEDADES), Err):
            return auth
        name = name.strip()
        if len(name) < 2:
            return Err(AppError.invalid("El nombre debe tener al menos 2 caracteres"))
        if await self._diseases.get_by_name(name) is not None:
            return Err(AppError.conflict("La enfermedad ya existe"))
        return Ok(await self._diseases.add(name, description))
