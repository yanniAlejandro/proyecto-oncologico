from uuid import UUID

from app.features.news.domain.model import EDITABLE_FIELDS, News, NewsDraft, NewsRepository
from app.shared.domain.actor import CONTENT_MANAGERS, Actor, require
from app.shared.domain.result import AppError, Err, Ok, Result

NOT_FOUND = "Noticia no encontrada"


def _clean(search: str | None) -> str | None:
    return search.strip() or None if search else None


class ListPublishedNews:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, search: str | None = None) -> list[News]:
        return await self._news.list(published_only=True, search=_clean(search))


class ListAllNews:
    """Incluye borradores: solo gestores de contenido."""

    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, actor: Actor | None, search: str | None = None) -> Result[list[News]]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        return Ok(await self._news.list(published_only=False, search=_clean(search)))


class GetPublishedNews:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, news_id: UUID) -> Result[News]:
        item = await self._news.get(news_id, published_only=True)
        return Ok(item) if item else Err(AppError.not_found(NOT_FOUND))


class CreateNews:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, actor: Actor | None, draft: NewsDraft) -> Result[News]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        return Ok(await self._news.add(draft, author_id=auth.value.id))


class UpdateNews:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, actor: Actor | None, news_id: UUID, changes: dict[str, object]) -> Result[News]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        allowed = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS}
        item = await self._news.update(news_id, allowed)
        return Ok(item) if item else Err(AppError.not_found(NOT_FOUND))


class DeleteNews:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def __call__(self, actor: Actor | None, news_id: UUID) -> Result[None]:
        if isinstance(auth := require(actor, CONTENT_MANAGERS), Err):
            return auth
        return Ok(None) if await self._news.delete(news_id) else Err(AppError.not_found(NOT_FOUND))
