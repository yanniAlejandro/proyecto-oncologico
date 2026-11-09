"""Casos de uso de publicaciones. Gestionar requiere el permiso «publicaciones»; leer es público."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.features.publications.domain.image_policy import MEDIA_TYPES, validate_image
from app.features.publications.domain.model import (
    EDITABLE_FIELDS,
    LinkPreview,
    LinkPreviewer,
    NewPublication,
    Publication,
    PublicationRepository,
    is_valid_url,
)
from app.shared.domain.actor import Actor, Section, require_section
from app.shared.domain.result import AppError, Err, Ok, Result
from app.shared.domain.storage import FileStorage

NOT_FOUND = "Publicación no encontrada"
INVALID_URL = "La URL debe empezar por http:// o https://"


@dataclass(frozen=True, slots=True)
class ImageSource:
    """De dónde sacar la imagen: subida a mano (tiene prioridad) o la og:image de la página."""

    upload: bytes | None = None
    url: str | None = None


def _clean_text(value: str | None) -> str | None:
    return (value or "").strip() or None


class ListPublications:
    def __init__(self, publications: PublicationRepository) -> None:
        self._publications = publications

    async def __call__(self, search: str | None = None) -> list[Publication]:
        return await self._publications.list(_clean_text(search))


class PreviewLink:
    """Lee título, descripción e imagen de la URL para autocompletar el formulario."""

    def __init__(self, previewer: LinkPreviewer) -> None:
        self._previewer = previewer

    async def __call__(self, actor: Actor | None, url: str) -> Result[LinkPreview | None]:
        if isinstance(auth := require_section(actor, Section.PUBLICACIONES), Err):
            return auth
        url = url.strip()
        if not is_valid_url(url):
            return Err(AppError.invalid(INVALID_URL))
        preview = await self._previewer.preview(url)
        return Ok(None if preview is None or preview.is_empty else preview)


class _ImageStore:
    """Guarda la imagen elegida; un fallo al descargar la og:image no impide publicar."""

    def __init__(self, storage: FileStorage, previewer: LinkPreviewer) -> None:
        self._storage = storage
        self._previewer = previewer

    async def save(self, source: ImageSource) -> Result[str | None]:
        if source.upload is not None:
            if isinstance(check := validate_image(source.upload), Err):
                return check  # subida a mano inválida: se avisa al usuario
            data = source.upload
        elif source.url and is_valid_url(source.url):
            data = await self._previewer.fetch_image(source.url)
            if data is None or isinstance(check := validate_image(data), Err):
                return Ok(None)
        else:
            return Ok(None)
        key = f"{uuid4().hex}{check.value}"
        self._storage.save(key, data)
        return Ok(key)


class CreatePublication:
    def __init__(self, publications: PublicationRepository, storage: FileStorage, previewer: LinkPreviewer) -> None:
        self._publications = publications
        self._storage = storage
        self._images = _ImageStore(storage, previewer)

    async def __call__(
        self,
        actor: Actor | None,
        *,
        title: str,
        url: str,
        description: str | None = None,
        image: ImageSource = ImageSource(),
    ) -> Result[Publication]:
        if isinstance(auth := require_section(actor, Section.PUBLICACIONES), Err):
            return auth
        title, url = title.strip(), url.strip()
        if len(title) < 3:
            return Err(AppError.invalid("El título debe tener al menos 3 caracteres"))
        if not is_valid_url(url):
            return Err(AppError.invalid(INVALID_URL))
        if isinstance(saved := await self._images.save(image), Err):
            return saved
        key = saved.value
        try:
            publication = await self._publications.add(
                NewPublication(
                    title=title, url=url, description=_clean_text(description), author_id=auth.value.id, image_key=key
                )
            )
        except Exception:
            if key:
                self._storage.delete(key)  # no dejar imágenes huérfanas
            raise
        return Ok(publication)


class UpdatePublication:
    def __init__(self, publications: PublicationRepository, storage: FileStorage, previewer: LinkPreviewer) -> None:
        self._publications = publications
        self._storage = storage
        self._images = _ImageStore(storage, previewer)

    async def __call__(
        self,
        actor: Actor | None,
        publication_id: UUID,
        changes: dict[str, object],
        *,
        image: ImageSource = ImageSource(),
        remove_image: bool = False,
    ) -> Result[Publication]:
        if isinstance(auth := require_section(actor, Section.PUBLICACIONES), Err):
            return auth
        current = await self._publications.get(publication_id)
        if current is None:
            return Err(AppError.not_found(NOT_FOUND))
        allowed = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS and v is not None}
        if "title" in allowed:
            allowed["title"] = str(allowed["title"]).strip()
            if len(str(allowed["title"])) < 3:
                return Err(AppError.invalid("El título debe tener al menos 3 caracteres"))
        if "url" in allowed:
            allowed["url"] = str(allowed["url"]).strip()
            if not is_valid_url(str(allowed["url"])):
                return Err(AppError.invalid(INVALID_URL))
        if "description" in allowed:
            allowed["description"] = _clean_text(str(allowed["description"]))

        new_key: str | None = None
        if image.upload is not None or image.url:
            if isinstance(saved := await self._images.save(image), Err):
                return saved
            new_key = saved.value
        if new_key or remove_image:
            allowed["image_key"] = new_key
        try:
            updated = await self._publications.update(publication_id, allowed)
        except Exception:
            if new_key:
                self._storage.delete(new_key)
            raise
        if updated is None:
            return Err(AppError.not_found(NOT_FOUND))
        if "image_key" in allowed and current.image_key:
            self._storage.delete(current.image_key)  # la imagen anterior ya no se usa
        return Ok(updated)


class DeletePublication:
    def __init__(self, publications: PublicationRepository, storage: FileStorage) -> None:
        self._publications = publications
        self._storage = storage

    async def __call__(self, actor: Actor | None, publication_id: UUID) -> Result[None]:
        if isinstance(auth := require_section(actor, Section.PUBLICACIONES), Err):
            return auth
        current = await self._publications.get(publication_id)
        if current is None or not await self._publications.delete(publication_id):
            return Err(AppError.not_found(NOT_FOUND))
        if current.image_key:
            self._storage.delete(current.image_key)
        return Ok(None)


@dataclass(frozen=True, slots=True)
class ImageToServe:
    path: Path
    media_type: str


class GetPublicationImage:
    def __init__(self, publications: PublicationRepository, storage: FileStorage) -> None:
        self._publications = publications
        self._storage = storage

    async def __call__(self, publication_id: UUID) -> Result[ImageToServe]:
        publication = await self._publications.get(publication_id)
        if publication is None or publication.image_key is None:
            return Err(AppError.not_found("Imagen no encontrada"))
        path = self._storage.path(publication.image_key)
        if path is None:
            return Err(AppError.not_found("Imagen no encontrada"))
        return Ok(ImageToServe(path=path, media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream")))
