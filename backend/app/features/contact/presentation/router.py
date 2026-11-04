from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.contact.application.use_cases import GetContact, UpdateContact
from app.features.contact.domain.model import ContactInfo, ContactRepository
from app.features.contact.infrastructure.repository import SqlContactRepository
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap

router = APIRouter()


def get_contact_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> ContactRepository:
    return SqlContactRepository(session)


Repo = Annotated[ContactRepository, Depends(get_contact_repository)]


class ContactOut(BaseModel):
    id: str
    organization_name: str
    address: str | None
    phone: str | None
    email: str | None
    schedule: str | None
    map_url: str | None

    @classmethod
    def of(cls, c: ContactInfo) -> "ContactOut":
        return cls(
            id=str(c.id),
            organization_name=c.organization_name,
            address=c.address,
            phone=c.phone,
            email=c.email,
            schedule=c.schedule,
            map_url=c.map_url,
        )


class ContactUpdate(BaseModel):
    organization_name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    schedule: str | None = None
    map_url: str | None = None


@router.get("", response_model=ContactOut)
async def get_contact(repo: Repo):
    return ContactOut.of(unwrap(await GetContact(repo)()))


@router.put("", response_model=ContactOut)
async def update_contact(payload: ContactUpdate, repo: Repo, actor: CurrentActor):
    return ContactOut.of(unwrap(await UpdateContact(repo)(actor, payload.model_dump(exclude_unset=True))))
