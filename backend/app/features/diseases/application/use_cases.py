from uuid import UUID

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


NOT_FOUND = "Enfermedad no encontrada"


class UpdateDisease:
    def __init__(self, diseases: DiseaseRepository) -> None:
        self._diseases = diseases

    async def __call__(
        self, actor: Actor | None, disease_id: UUID, *, name: str | None = None, description: str | None = None
    ) -> Result[Disease]:
        if isinstance(auth := require_section(actor, Section.ENFERMEDADES), Err):
            return auth
        if await self._diseases.get(disease_id) is None:
            return Err(AppError.not_found(NOT_FOUND))
        changes: dict[str, object] = {}
        if name is not None:
            name = name.strip()
            if len(name) < 2:
                return Err(AppError.invalid("El nombre debe tener al menos 2 caracteres"))
            other = await self._diseases.get_by_name(name)
            if other is not None and other.id != disease_id:
                return Err(AppError.conflict("La enfermedad ya existe"))
            changes["name"] = name
        if description is not None:
            changes["description"] = description.strip() or None
        updated = await self._diseases.update(disease_id, changes)
        return Ok(updated) if updated else Err(AppError.not_found(NOT_FOUND))


class DeleteDisease:
    """No se borra una enfermedad con guías o protocolos asociados."""

    def __init__(self, diseases: DiseaseRepository) -> None:
        self._diseases = diseases

    async def __call__(self, actor: Actor | None, disease_id: UUID) -> Result[None]:
        if isinstance(auth := require_section(actor, Section.ENFERMEDADES), Err):
            return auth
        if await self._diseases.get(disease_id) is None:
            return Err(AppError.not_found(NOT_FOUND))
        if (used := await self._diseases.usage(disease_id)) > 0:
            return Err(AppError.conflict(f"No se puede eliminar: la usan {used} guías o protocolos"))
        await self._diseases.delete(disease_id)
        return Ok(None)
