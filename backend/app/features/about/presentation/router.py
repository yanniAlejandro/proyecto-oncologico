from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.about.application import use_cases as uc
from app.features.about.domain.model import AboutRepository, AboutSection
from app.features.about.infrastructure.repository import SqlAboutRepository
from app.features.auth.presentation.deps import CurrentActor
from app.shared.domain.image_policy import MAX_IMAGE_BYTES
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap
from app.shared.presentation.storage import Storage

router = APIRouter()


def get_about_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> AboutRepository:
    return SqlAboutRepository(session)


Repo = Annotated[AboutRepository, Depends(get_about_repository)]


class AboutSectionOut(BaseModel):
    id: str
    slug: str
    title: str
    body: str
    sort_order: int
    image_url: str | None
    updated_at: datetime

    @classmethod
    def of(cls, s: AboutSection) -> "AboutSectionOut":
        version = int(s.updated_at.timestamp())
        return cls(
            id=str(s.id),
            slug=s.slug,
            title=s.title,
            body=s.body,
            sort_order=s.sort_order,
            image_url=f"/api/v1/about/{s.id}/image?v={version}" if s.has_image else None,
            updated_at=s.updated_at,
        )


async def _read(image: UploadFile | None) -> bytes | None:
    return await image.read(MAX_IMAGE_BYTES + 1) if image is not None and image.filename else None


@router.get("", response_model=list[AboutSectionOut])
async def list_sections(repo: Repo):
    return [AboutSectionOut.of(s) for s in await uc.ListAboutSections(repo)()]


@router.post("", response_model=AboutSectionOut, status_code=status.HTTP_201_CREATED)
async def create_section(
    repo: Repo,
    storage: Storage,
    actor: CurrentActor,
    title: Annotated[str, Form(max_length=255)],
    body: Annotated[str, Form()],
    sort_order: Annotated[int | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    result = await uc.CreateAboutSection(repo, storage)(
        actor, title=title, body=body, sort_order=sort_order, image=await _read(image)
    )
    return AboutSectionOut.of(unwrap(result))


@router.put("/{section_id}", response_model=AboutSectionOut)
async def update_section(
    section_id: UUID,
    repo: Repo,
    storage: Storage,
    actor: CurrentActor,
    title: Annotated[str | None, Form(max_length=255)] = None,
    body: Annotated[str | None, Form()] = None,
    sort_order: Annotated[int | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    remove_image: Annotated[bool, Form()] = False,
):
    changes = {"title": title, "body": body, "sort_order": sort_order}
    result = await uc.UpdateAboutSection(repo, storage)(
        actor, section_id, changes, image=await _read(image), remove_image=remove_image
    )
    return AboutSectionOut.of(unwrap(result))


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(section_id: UUID, repo: Repo, storage: Storage, actor: CurrentActor):
    unwrap(await uc.DeleteAboutSection(repo, storage)(actor, section_id))


@router.get("/{section_id}/image")
async def get_section_image(section_id: UUID, repo: Repo, storage: Storage):
    served = unwrap(await uc.GetAboutImage(repo, storage)(section_id))
    return FileResponse(
        served.path,
        media_type=served.media_type,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"},
    )
