from urllib.parse import urlparse
from uuid import UUID

from app.features.interest_links.domain.model import EDITABLE_FIELDS, InterestLink, InterestLinkRepository
from app.shared.domain.actor import Actor, Section, require_section
from app.shared.domain.result import AppError, Err, Ok, Result

NOT_FOUND = "Enlace no encontrado"


def _valid_url(url: object) -> bool:
    parsed = urlparse(str(url))
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class ListActiveLinks:
    def __init__(self, links: InterestLinkRepository) -> None:
        self._links = links

    async def __call__(self) -> list[InterestLink]:
        return await self._links.list_active()


class CreateLink:
    def __init__(self, links: InterestLinkRepository) -> None:
        self._links = links

    async def __call__(self, actor: Actor | None, data: dict[str, object]) -> Result[InterestLink]:
        if isinstance(auth := require_section(actor, Section.ENLACES), Err):
            return auth
        if not _valid_url(data.get("url")):
            return Err(AppError.invalid("La URL debe empezar por http:// o https://"))
        return Ok(await self._links.add({k: v for k, v in data.items() if k in EDITABLE_FIELDS}))


class UpdateLink:
    def __init__(self, links: InterestLinkRepository) -> None:
        self._links = links

    async def __call__(self, actor: Actor | None, link_id: UUID, changes: dict[str, object]) -> Result[InterestLink]:
        if isinstance(auth := require_section(actor, Section.ENLACES), Err):
            return auth
        if "url" in changes and not _valid_url(changes["url"]):
            return Err(AppError.invalid("La URL debe empezar por http:// o https://"))
        link = await self._links.update(link_id, {k: v for k, v in changes.items() if k in EDITABLE_FIELDS})
        return Ok(link) if link else Err(AppError.not_found(NOT_FOUND))


class DeleteLink:
    def __init__(self, links: InterestLinkRepository) -> None:
        self._links = links

    async def __call__(self, actor: Actor | None, link_id: UUID) -> Result[None]:
        if isinstance(auth := require_section(actor, Section.ENLACES), Err):
            return auth
        return Ok(None) if await self._links.delete(link_id) else Err(AppError.not_found(NOT_FOUND))
