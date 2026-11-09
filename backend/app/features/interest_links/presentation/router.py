from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.interest_links.application import use_cases as uc
from app.features.interest_links.domain.model import InterestLink, InterestLinkRepository
from app.features.interest_links.infrastructure.repository import SqlInterestLinkRepository
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap

router = APIRouter()


def get_link_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> InterestLinkRepository:
    return SqlInterestLinkRepository(session)


Repo = Annotated[InterestLinkRepository, Depends(get_link_repository)]


class InterestLinkCreate(BaseModel):
    title: str
    url: str
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class InterestLinkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class InterestLinkOut(BaseModel):
    id: str
    title: str
    url: str
    description: str | None
    sort_order: int
    is_active: bool

    @classmethod
    def of(cls, link: InterestLink) -> "InterestLinkOut":
        return cls(
            id=str(link.id),
            title=link.title,
            url=link.url,
            description=link.description,
            sort_order=link.sort_order,
            is_active=link.is_active,
        )


@router.get("", response_model=list[InterestLinkOut])
async def list_links(repo: Repo):
    return [InterestLinkOut.of(link) for link in await uc.ListActiveLinks(repo)()]


@router.get("/manage", response_model=list[InterestLinkOut])
async def list_all_links(repo: Repo, actor: CurrentActor):
    return [InterestLinkOut.of(link) for link in unwrap(await uc.ListAllLinks(repo)(actor))]


@router.post("", response_model=InterestLinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(payload: InterestLinkCreate, repo: Repo, actor: CurrentActor):
    return InterestLinkOut.of(unwrap(await uc.CreateLink(repo)(actor, payload.model_dump())))


@router.put("/{link_id}", response_model=InterestLinkOut)
async def update_link(link_id: UUID, payload: InterestLinkUpdate, repo: Repo, actor: CurrentActor):
    changes = payload.model_dump(exclude_unset=True)
    return InterestLinkOut.of(unwrap(await uc.UpdateLink(repo)(actor, link_id, changes)))


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(link_id: UUID, repo: Repo, actor: CurrentActor):
    unwrap(await uc.DeleteLink(repo)(actor, link_id))
