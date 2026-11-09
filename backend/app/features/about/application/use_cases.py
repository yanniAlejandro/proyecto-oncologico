"""Leer es público (es la portada). Gestionar requiere el permiso «quienes_somos»."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.features.about.domain.model import (
    EDITABLE_FIELDS,
    MAX_BODY,
    AboutRepository,
    AboutSection,
    NewAboutSection,
    slugify,
)
from app.shared.domain.actor import Actor, Section, require_section
from app.shared.domain.image_policy import MEDIA_TYPES, validate_image
from app.shared.domain.result import AppError, Err, Ok, Result
from app.shared.domain.storage import FileStorage

NOT_FOUND = "Apartado no encontrado"


def _validate(title: str | None, body: str | None) -> Err | None:
    if title is not None and len(title.strip()) < 3:
        return Err(AppError.invalid("El título debe tener al menos 3 caracteres"))
    if body is not None and not body.strip():
        return Err(AppError.invalid("El texto no puede estar vacío"))
    if body is not None and len(body) > MAX_BODY:
        return Err(AppError.invalid(f"El texto supera los {MAX_BODY} caracteres"))
    return None


async def _unique_slug(repo: AboutRepository, title: str, exclude: UUID | None = None) -> str:
    base = slugify(title)
    slug, n = base, 2
    while await repo.slug_exists(slug, exclude):
        slug, n = f"{base}-{n}", n + 1
    return slug


def _store_image(storage: FileStorage, data: bytes) -> Result[str]:
    if isinstance(check := validate_image(data), Err):
        return check
    key = f"{uuid4().hex}{check.value}"
    storage.save(key, data)
    return Ok(key)


class ListAboutSections:
    def __init__(self, repo: AboutRepository) -> None:
        self._repo = repo

    async def __call__(self) -> list[AboutSection]:
        return await self._repo.list()


class CreateAboutSection:
    def __init__(self, repo: AboutRepository, storage: FileStorage) -> None:
        self._repo = repo
        self._storage = storage

    async def __call__(
        self, actor: Actor | None, *, title: str, body: str, sort_order: int | None = None, image: bytes | None = None
    ) -> Result[AboutSection]:
        if isinstance(auth := require_section(actor, Section.QUIENES_SOMOS), Err):
            return auth
        if bad := _validate(title, body):
            return bad
        key = None
        if image is not None:
            if isinstance(stored := _store_image(self._storage, image), Err):
                return stored
            key = stored.value
        if sort_order is None:
            existing = await self._repo.list()
            sort_order = max((s.sort_order for s in existing), default=0) + 10
        try:
            section = await self._repo.add(
                NewAboutSection(
                    slug=await _unique_slug(self._repo, title),
                    title=title.strip(),
                    body=body.strip(),
                    sort_order=sort_order,
                    image_key=key,
                )
            )
        except Exception:
            if key:
                self._storage.delete(key)
            raise
        return Ok(section)


class UpdateAboutSection:
    def __init__(self, repo: AboutRepository, storage: FileStorage) -> None:
        self._repo = repo
        self._storage = storage

    async def __call__(
        self,
        actor: Actor | None,
        section_id: UUID,
        changes: dict[str, object],
        *,
        image: bytes | None = None,
        remove_image: bool = False,
    ) -> Result[AboutSection]:
        if isinstance(auth := require_section(actor, Section.QUIENES_SOMOS), Err):
            return auth
        current = await self._repo.get(section_id)
        if current is None:
            return Err(AppError.not_found(NOT_FOUND))
        allowed = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS and v is not None}
        title = allowed.get("title")
        body = allowed.get("body")
        if bad := _validate(title if isinstance(title, str) else None, body if isinstance(body, str) else None):
            return bad
        if isinstance(title, str):
            allowed["title"] = title.strip()
            # La ancla sigue al título para que el índice sea legible.
            allowed["slug"] = await _unique_slug(self._repo, title, exclude=section_id)
        if isinstance(body, str):
            allowed["body"] = body.strip()

        new_key = None
        if image is not None:
            if isinstance(stored := _store_image(self._storage, image), Err):
                return stored
            new_key = stored.value
            allowed["image_key"] = new_key
        elif remove_image:
            allowed["image_key"] = None
        try:
            updated = await self._repo.update(section_id, allowed)
        except Exception:
            if new_key:
                self._storage.delete(new_key)
            raise
        if updated is None:
            return Err(AppError.not_found(NOT_FOUND))
        if "image_key" in allowed and current.image_key:
            self._storage.delete(current.image_key)
        return Ok(updated)


class DeleteAboutSection:
    def __init__(self, repo: AboutRepository, storage: FileStorage) -> None:
        self._repo = repo
        self._storage = storage

    async def __call__(self, actor: Actor | None, section_id: UUID) -> Result[None]:
        if isinstance(auth := require_section(actor, Section.QUIENES_SOMOS), Err):
            return auth
        current = await self._repo.get(section_id)
        if current is None or not await self._repo.delete(section_id):
            return Err(AppError.not_found(NOT_FOUND))
        if current.image_key:
            self._storage.delete(current.image_key)
        return Ok(None)


@dataclass(frozen=True, slots=True)
class ImageToServe:
    path: Path
    media_type: str


class GetAboutImage:
    def __init__(self, repo: AboutRepository, storage: FileStorage) -> None:
        self._repo = repo
        self._storage = storage

    async def __call__(self, section_id: UUID) -> Result[ImageToServe]:
        section = await self._repo.get(section_id)
        path = self._storage.path(section.image_key) if section and section.image_key else None
        if path is None:
            return Err(AppError.not_found("Imagen no encontrada"))
        return Ok(ImageToServe(path=path, media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream")))
