from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.publications.application import use_cases as uc
from app.features.publications.domain.image_policy import MAX_IMAGE_BYTES
from app.features.publications.domain.model import LinkPreviewer, Publication, PublicationRepository
from app.features.publications.infrastructure.http_previewer import HttpLinkPreviewer
from app.features.publications.infrastructure.repository import SqlPublicationRepository
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap
from app.shared.presentation.storage import Storage

router = APIRouter()


def get_publication_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> PublicationRepository:
    return SqlPublicationRepository(session)


def get_link_previewer() -> LinkPreviewer:
    return HttpLinkPreviewer()


Repo = Annotated[PublicationRepository, Depends(get_publication_repository)]
Previewer = Annotated[LinkPreviewer, Depends(get_link_previewer)]


class PublicationOut(BaseModel):
    id: str
    title: str
    url: str
    domain: str
    description: str | None
    image_url: str | None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, p: Publication) -> "PublicationOut":
        # La imagen se sirve desde nuestro almacenamiento (nunca se enlaza la original).
        version = int(p.updated_at.timestamp())
        return cls(
            id=str(p.id),
            title=p.title,
            url=p.url,
            domain=p.domain,
            description=p.description,
            image_url=f"/api/v1/publications/{p.id}/image?v={version}" if p.has_image else None,
            author_name=p.author_name,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


class PreviewIn(BaseModel):
    url: str = Field(min_length=8, max_length=1000)


class PreviewOut(BaseModel):
    found: bool
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    site_name: str | None = None


async def _read_image(image: UploadFile | None) -> bytes | None:
    if image is None or not image.filename:
        return None
    return await image.read(MAX_IMAGE_BYTES + 1)


@router.get("", response_model=list[PublicationOut])
async def list_publications(repo: Repo, search: str | None = Query(None)):
    return [PublicationOut.of(p) for p in await uc.ListPublications(repo)(search)]


@router.post("/preview", response_model=PreviewOut)
async def preview_link(payload: PreviewIn, previewer: Previewer, actor: CurrentActor):
    preview = unwrap(await uc.PreviewLink(previewer)(actor, payload.url))
    if preview is None:
        return PreviewOut(found=False)
    return PreviewOut(
        found=True,
        title=preview.title,
        description=preview.description,
        image_url=preview.image_url,
        site_name=preview.site_name,
    )


@router.post("", response_model=PublicationOut, status_code=status.HTTP_201_CREATED)
async def create_publication(
    repo: Repo,
    storage: Storage,
    previewer: Previewer,
    actor: CurrentActor,
    title: Annotated[str, Form(max_length=500)],
    url: Annotated[str, Form(max_length=1000)],
    description: Annotated[str | None, Form()] = None,
    image_url: Annotated[str | None, Form(max_length=2000)] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    """Multipart. Imagen: ``image`` (subida a mano) o ``image_url`` (la og:image, que se descarga y se guarda)."""
    source = uc.ImageSource(upload=await _read_image(image), url=image_url)
    result = await uc.CreatePublication(repo, storage, previewer)(
        actor, title=title, url=url, description=description, image=source
    )
    return PublicationOut.of(unwrap(result))


@router.put("/{publication_id}", response_model=PublicationOut)
async def update_publication(
    publication_id: UUID,
    repo: Repo,
    storage: Storage,
    previewer: Previewer,
    actor: CurrentActor,
    title: Annotated[str | None, Form(max_length=500)] = None,
    url: Annotated[str | None, Form(max_length=1000)] = None,
    description: Annotated[str | None, Form()] = None,
    image_url: Annotated[str | None, Form(max_length=2000)] = None,
    image: Annotated[UploadFile | None, File()] = None,
    remove_image: Annotated[bool, Form()] = False,
):
    source = uc.ImageSource(upload=await _read_image(image), url=image_url)
    changes = {"title": title, "url": url, "description": description}
    result = await uc.UpdatePublication(repo, storage, previewer)(
        actor, publication_id, changes, image=source, remove_image=remove_image
    )
    return PublicationOut.of(unwrap(result))


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_publication(publication_id: UUID, repo: Repo, storage: Storage, actor: CurrentActor):
    unwrap(await uc.DeletePublication(repo, storage)(actor, publication_id))


@router.get("/{publication_id}/image")
async def get_publication_image(publication_id: UUID, repo: Repo, storage: Storage):
    served = unwrap(await uc.GetPublicationImage(repo, storage)(publication_id))
    return FileResponse(
        served.path,
        media_type=served.media_type,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"},
    )
