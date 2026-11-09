"""Leer es público. Gestionar requiere el permiso «linea_ayuda»."""

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from app.features.helpline.domain.model import (
    DEFAULT_CONFIG,
    HelplineConfig,
    HelplineRepository,
    Professional,
    TimeSlot,
    is_available,
    next_opening,
    sort_slots,
)
from app.shared.domain.actor import Actor, Section, require_section
from app.shared.domain.result import AppError, Err, Ok, Result

NOT_FOUND = "Profesional no encontrado"
PROFESSIONAL_FIELDS = frozenset({"full_name", "specialty", "phone", "sort_order", "is_active", "slots"})


def _phone_ok(phone: str) -> bool:
    digits = sum(c.isdigit() for c in phone)
    return 6 <= digits <= 20 and all(c.isdigit() or c in " +-()." for c in phone)


@dataclass(frozen=True, slots=True)
class Availability:
    available_now: bool
    next_opening: datetime | None


def availability(slots: list[TimeSlot], now: datetime) -> Availability:
    available = is_available(slots, now)
    return Availability(available, None if available else next_opening(slots, now))


@dataclass(frozen=True, slots=True)
class HelplineView:
    config: HelplineConfig
    status: Availability
    professionals: list[tuple[Professional, Availability]]


class GetHelpline:
    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(self, now: datetime) -> HelplineView:
        config = await self._repo.get_config() or DEFAULT_CONFIG
        pros = await self._repo.list_professionals(active_only=True)
        return HelplineView(
            config=config,
            status=availability(config.slots, now),
            professionals=[(p, availability(p.slots, now)) for p in pros],
        )


class UpdateHelplineConfig:
    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(self, actor: Actor | None, changes: dict[str, object]) -> Result[HelplineConfig]:
        if isinstance(auth := require_section(actor, Section.LINEA_AYUDA), Err):
            return auth
        current = await self._repo.get_config() or DEFAULT_CONFIG
        allowed = {k: v for k, v in changes.items() if v is not None and k in HelplineConfig.__dataclass_fields__}
        if "phone" in allowed and not _phone_ok(str(allowed["phone"])):
            return Err(AppError.invalid("Teléfono no válido"))
        if allowed.get("emergency_phone") == "":
            allowed["emergency_phone"] = None
        elif "emergency_phone" in allowed and not _phone_ok(str(allowed["emergency_phone"])):
            return Err(AppError.invalid("Teléfono de urgencias no válido"))
        for key in ("label", "off_hours_message"):
            if key in allowed and not str(allowed[key]).strip():
                return Err(AppError.invalid("El texto no puede estar vacío"))
        if "slots" in allowed:
            allowed["slots"] = sort_slots(list(allowed["slots"]))  # type: ignore[call-overload]
        return Ok(await self._repo.save_config(replace(current, **allowed)))


def _validate_professional(data: dict[str, object], *, partial: bool) -> Err | None:
    for key in ("full_name", "specialty"):
        if (key in data or not partial) and len(str(data.get(key, "")).strip()) < 2:
            return Err(AppError.invalid("Nombre y especialidad son obligatorios"))
    if ("phone" in data or not partial) and not _phone_ok(str(data.get("phone", ""))):
        return Err(AppError.invalid("Teléfono no válido"))
    return None


class ListProfessionalsForManagement:
    """Incluye inactivos."""

    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(self, actor: Actor | None) -> Result[list[Professional]]:
        if isinstance(auth := require_section(actor, Section.LINEA_AYUDA), Err):
            return auth
        return Ok(await self._repo.list_professionals(active_only=False))


class CreateProfessional:
    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(self, actor: Actor | None, data: dict[str, object]) -> Result[Professional]:
        if isinstance(auth := require_section(actor, Section.LINEA_AYUDA), Err):
            return auth
        clean = {k: v for k, v in data.items() if k in PROFESSIONAL_FIELDS and v is not None}
        if bad := _validate_professional(clean, partial=False):
            return bad
        for key in ("full_name", "specialty", "phone"):
            clean[key] = str(clean[key]).strip()
        clean["slots"] = sort_slots(list(clean.get("slots", [])))  # type: ignore[call-overload]
        return Ok(await self._repo.add_professional(clean))


class UpdateProfessional:
    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(
        self, actor: Actor | None, professional_id: UUID, changes: dict[str, object]
    ) -> Result[Professional]:
        if isinstance(auth := require_section(actor, Section.LINEA_AYUDA), Err):
            return auth
        clean = {k: v for k, v in changes.items() if k in PROFESSIONAL_FIELDS and v is not None}
        if bad := _validate_professional(clean, partial=True):
            return bad
        for key in ("full_name", "specialty", "phone"):
            if key in clean:
                clean[key] = str(clean[key]).strip()
        if "slots" in clean:
            clean["slots"] = sort_slots(list(clean["slots"]))  # type: ignore[call-overload]
        updated = await self._repo.update_professional(professional_id, clean)
        return Ok(updated) if updated else Err(AppError.not_found(NOT_FOUND))


class DeleteProfessional:
    def __init__(self, repo: HelplineRepository) -> None:
        self._repo = repo

    async def __call__(self, actor: Actor | None, professional_id: UUID) -> Result[None]:
        if isinstance(auth := require_section(actor, Section.LINEA_AYUDA), Err):
            return auth
        return Ok(None) if await self._repo.delete_professional(professional_id) else Err(AppError.not_found(NOT_FOUND))
