from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.news.application import use_cases as uc
from app.features.news.domain.model import News, NewsDraft, NewsRepository
from app.features.news.infrastructure.repository import SqlNewsRepository
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap

router = APIRouter()


def get_news_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> NewsRepository:
    return SqlNewsRepository(session)


Repo = Annotated[NewsRepository, Depends(get_news_repository)]


class NewsCreate(BaseModel):
    title: str = Field(min_length=3)
    summary: str | None = None
    content: str = Field(min_length=10)
    is_published: bool = True


class NewsUpdate(BaseModel):
    title: str | None = Field(None, min_length=3)
    summary: str | None = None
    content: str | None = Field(None, min_length=10)
    is_published: bool | None = None


class NewsOut(BaseModel):
    id: str
    title: str
    summary: str | None
    content: str
    author_name: str | None = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, n: News) -> "NewsOut":
        return cls(
            id=str(n.id),
            title=n.title,
            summary=n.summary,
            content=n.content,
            author_name=n.author_name,
            is_published=n.is_published,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )


@router.get("", response_model=list[NewsOut])
async def list_news(repo: Repo, search: str | None = Query(None)):
    return [NewsOut.of(n) for n in await uc.ListPublishedNews(repo)(search)]


@router.get("/manage", response_model=list[NewsOut])
async def list_news_manage(repo: Repo, actor: CurrentActor, search: str | None = Query(None)):
    return [NewsOut.of(n) for n in unwrap(await uc.ListAllNews(repo)(actor, search))]


@router.get("/{news_id}", response_model=NewsOut)
async def get_news(news_id: UUID, repo: Repo):
    return NewsOut.of(unwrap(await uc.GetPublishedNews(repo)(news_id)))


@router.post("", response_model=NewsOut, status_code=status.HTTP_201_CREATED)
async def create_news(payload: NewsCreate, repo: Repo, actor: CurrentActor):
    return NewsOut.of(unwrap(await uc.CreateNews(repo)(actor, NewsDraft(**payload.model_dump()))))


@router.put("/{news_id}", response_model=NewsOut)
async def update_news(news_id: UUID, payload: NewsUpdate, repo: Repo, actor: CurrentActor):
    changes = payload.model_dump(exclude_unset=True)
    return NewsOut.of(unwrap(await uc.UpdateNews(repo)(actor, news_id, changes)))


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: UUID, repo: Repo, actor: CurrentActor):
    unwrap(await uc.DeleteNews(repo)(actor, news_id))
