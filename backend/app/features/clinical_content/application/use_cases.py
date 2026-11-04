from uuid import UUID

from app.features.clinical_content.domain.model import (
    EDITABLE_FIELDS,
    ClinicalContentRepository,
    ClinicalDoc,
    ClinicalDraft,
    ContentKind,
)
from app.features.diseases.domain.model import DiseaseRepository
from app.shared.domain.actor import CONTENT_MANAGERS, Actor, require
from app.shared.domain.result import AppError, Err, Ok, Result

DISEASE_NOT_FOUND = "Enfermedad no encontrada"


def _can_read(kind: ContentKind, actor: Actor | None) -> Result[None]:
    if kind.readers is None:
        return Ok(None)
    if isinstance(auth := require(actor, kind.readers), Err):
        return auth
    return Ok(None)


class ListClinicalDocs:
    def __init__(self, kind: ContentKind, docs: ClinicalContentRepository) -> None:
        self._kind = kind
        self._docs = docs

    async def __call__(self, actor: Actor | None, search: str | None = None) -> Result[list[ClinicalDoc]]:
        if isinstance(access := _can_read(self._kind, actor), Err):
            return access
        return Ok(await self._docs.list(search.strip() or None if search else None))


class GetClinicalDoc:
    def __init__(self, kind: ContentKind, docs: ClinicalContentRepository) -> None:
        self._kind = kind
        self._docs = docs

    async def __call__(self, actor: Actor | None, doc_id: UUID) -> Result[ClinicalDoc]:
        if isinstance(access := _can_read(self._kind, actor), Err):
            return access
        doc = await self._docs.get(doc_id)
        return Ok(doc) if doc else Err(AppError.not_found(self._kind.not_found_message))


class CreateClinicalDoc:
    def __init__(self, docs: ClinicalContentRepository, diseases: DiseaseRepository) -> None:
        self._docs = docs
        self._diseases = diseases

    async def __call__(self, actor: Actor | None, draft: ClinicalDraft) -> Result[ClinicalDoc]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        if await self._diseases.get(draft.disease_id) is None:
            return Err(AppError.invalid(DISEASE_NOT_FOUND))
        return Ok(await self._docs.add(draft, author_id=auth.value.id))


class UpdateClinicalDoc:
    def __init__(self, kind: ContentKind, docs: ClinicalContentRepository, diseases: DiseaseRepository) -> None:
        self._kind = kind
        self._docs = docs
        self._diseases = diseases

    async def __call__(self, actor: Actor | None, doc_id: UUID, changes: dict[str, object]) -> Result[ClinicalDoc]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        allowed = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS and v is not None}
        disease_id = allowed.get("disease_id")
        if isinstance(disease_id, UUID) and await self._diseases.get(disease_id) is None:
            return Err(AppError.invalid(DISEASE_NOT_FOUND))
        doc = await self._docs.update(doc_id, allowed)
        return Ok(doc) if doc else Err(AppError.not_found(self._kind.not_found_message))


class DeleteClinicalDoc:
    def __init__(self, kind: ContentKind, docs: ClinicalContentRepository) -> None:
        self._kind = kind
        self._docs = docs

    async def __call__(self, actor: Actor | None, doc_id: UUID) -> Result[None]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        if await self._docs.delete(doc_id):
            return Ok(None)
        return Err(AppError.not_found(self._kind.not_found_message))
