from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.presentation.deps import CurrentActor
from app.features.helpline.application import use_cases as uc
from app.features.helpline.domain.model import (
    MIN_DAILY_HOURS,
    WEEKDAYS,
    HelplineConfig,
    HelplineRepository,
    Professional,
    TimeSlot,
    daily_hours,
    parse_slot,
    slot_to_json,
)
from app.features.helpline.infrastructure.repository import SqlHelplineRepository
from app.shared.infrastructure.database import get_session
from app.shared.presentation.errors import unwrap

router = APIRouter()


def get_helpline_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> HelplineRepository:
    return SqlHelplineRepository(session)


def get_clock() -> datetime:
    return datetime.now(UTC)


Repo = Annotated[HelplineRepository, Depends(get_helpline_repository)]
Now = Annotated[datetime, Depends(get_clock)]


class SlotIO(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start: str = Field(pattern=r"^\d{2}:\d{2}$")
    end: str = Field(pattern=r"^\d{2}:\d{2}$")

    @model_validator(mode="after")
    def _check(self) -> "SlotIO":
        if parse_slot(self.model_dump()) is None:
            raise ValueError("Franja no válida: la hora de inicio debe ser anterior a la de fin")
        return self

    def to_domain(self) -> TimeSlot:
        slot = parse_slot(self.model_dump())
        assert slot is not None  # validado en _check
        return slot


def _slots_in(slots: list[SlotIO] | None) -> list[TimeSlot] | None:
    return None if slots is None else [s.to_domain() for s in slots]


def _slots_out(slots: list[TimeSlot]) -> list[dict[str, object]]:
    return [slot_to_json(s) for s in slots]


class StatusOut(BaseModel):
    available_now: bool
    next_opening: datetime | None


class ProfessionalOut(BaseModel):
    id: str
    full_name: str
    specialty: str
    phone: str
    sort_order: int
    is_active: bool
    slots: list[dict[str, object]]
    status: StatusOut | None = None

    @classmethod
    def of(cls, p: Professional, status: uc.Availability | None = None) -> "ProfessionalOut":
        return cls(
            id=str(p.id),
            full_name=p.full_name,
            specialty=p.specialty,
            phone=p.phone,
            sort_order=p.sort_order,
            is_active=p.is_active,
            slots=_slots_out(p.slots),
            status=StatusOut(available_now=status.available_now, next_opening=status.next_opening) if status else None,
        )


class ConfigOut(BaseModel):
    phone: str
    label: str
    off_hours_message: str
    emergency_phone: str | None
    slots: list[dict[str, object]]
    daily_hours: list[float]
    meets_minimum: bool
    """Cada día cubre al menos MIN_DAILY_HOURS (estándar de 6 h diarias)."""

    @classmethod
    def of(cls, c: HelplineConfig) -> "ConfigOut":
        hours = daily_hours(c.slots)
        return cls(
            phone=c.phone,
            label=c.label,
            off_hours_message=c.off_hours_message,
            emergency_phone=c.emergency_phone,
            slots=_slots_out(c.slots),
            daily_hours=hours,
            meets_minimum=all(h >= MIN_DAILY_HOURS for h in hours),
        )


class HelplineOut(BaseModel):
    config: ConfigOut
    status: StatusOut
    professionals: list[ProfessionalOut]
    weekdays: list[str] = list(WEEKDAYS)


class ConfigIn(BaseModel):
    phone: str | None = Field(None, max_length=50)
    label: str | None = Field(None, max_length=255)
    off_hours_message: str | None = None
    emergency_phone: str | None = Field(None, max_length=50)
    slots: list[SlotIO] | None = None


class ProfessionalIn(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    specialty: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    sort_order: int | None = None
    is_active: bool | None = None
    slots: list[SlotIO] | None = None

    def changes(self) -> dict[str, object]:
        data = self.model_dump(exclude_unset=True, exclude={"slots"})
        if self.slots is not None:
            data["slots"] = _slots_in(self.slots)
        return data


@router.get("", response_model=HelplineOut)
async def get_helpline(repo: Repo, now: Now):
    view = await uc.GetHelpline(repo)(now)
    return HelplineOut(
        config=ConfigOut.of(view.config),
        status=StatusOut(available_now=view.status.available_now, next_opening=view.status.next_opening),
        professionals=[ProfessionalOut.of(p, s) for p, s in view.professionals],
    )


@router.put("", response_model=ConfigOut)
async def update_helpline(payload: ConfigIn, repo: Repo, actor: CurrentActor):
    changes = payload.model_dump(exclude_unset=True, exclude={"slots"})
    if payload.slots is not None:
        changes["slots"] = _slots_in(payload.slots)
    return ConfigOut.of(unwrap(await uc.UpdateHelplineConfig(repo)(actor, changes)))


@router.get("/professionals", response_model=list[ProfessionalOut])
async def list_professionals(repo: Repo, actor: CurrentActor):
    return [ProfessionalOut.of(p) for p in unwrap(await uc.ListProfessionalsForManagement(repo)(actor))]


@router.post("/professionals", response_model=ProfessionalOut, status_code=status.HTTP_201_CREATED)
async def create_professional(payload: ProfessionalIn, repo: Repo, actor: CurrentActor):
    return ProfessionalOut.of(unwrap(await uc.CreateProfessional(repo)(actor, payload.changes())))


@router.put("/professionals/{professional_id}", response_model=ProfessionalOut)
async def update_professional(professional_id: UUID, payload: ProfessionalIn, repo: Repo, actor: CurrentActor):
    return ProfessionalOut.of(unwrap(await uc.UpdateProfessional(repo)(actor, professional_id, payload.changes())))


@router.delete("/professionals/{professional_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_professional(professional_id: UUID, repo: Repo, actor: CurrentActor):
    unwrap(await uc.DeleteProfessional(repo)(actor, professional_id))
