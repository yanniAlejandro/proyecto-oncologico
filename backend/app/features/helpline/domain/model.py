"""Línea de ayuda: teléfono del hospital + profesionales localizables, cada uno con sus franjas.

Estándar acordado: al menos 6 horas diarias de atención a pacientes y familias.
La disponibilidad se calcula con la hora de La Habana.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

HAVANA = ZoneInfo("America/Havana")
WEEKDAYS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
MIN_DAILY_HOURS = 6


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """Franja semanal: ``weekday`` 0 = lunes … 6 = domingo, [start, end)."""

    weekday: int
    start: time
    end: time

    def contains(self, moment: datetime) -> bool:
        return moment.weekday() == self.weekday and self.start <= moment.time() < self.end

    @property
    def hours(self) -> float:
        return (datetime.combine(datetime.min, self.end) - datetime.combine(datetime.min, self.start)) / timedelta(
            hours=1
        )


def parse_slot(raw: dict[str, object]) -> TimeSlot | None:
    """Desde JSON ({weekday, start "HH:MM", end "HH:MM"}); ``None`` si es inválida."""
    try:
        weekday = int(raw["weekday"])  # type: ignore[call-overload]
        start = time.fromisoformat(str(raw["start"]))
        end = time.fromisoformat(str(raw["end"]))
    except (KeyError, TypeError, ValueError):
        return None
    if not 0 <= weekday <= 6 or start >= end:
        return None
    return TimeSlot(weekday, start.replace(second=0, microsecond=0), end.replace(second=0, microsecond=0))


def slot_to_json(slot: TimeSlot) -> dict[str, object]:
    return {"weekday": slot.weekday, "start": slot.start.strftime("%H:%M"), "end": slot.end.strftime("%H:%M")}


def sort_slots(slots: list[TimeSlot]) -> list[TimeSlot]:
    return sorted(slots, key=lambda s: (s.weekday, s.start))


def is_available(slots: list[TimeSlot], moment: datetime) -> bool:
    local = moment.astimezone(HAVANA)
    return any(s.contains(local) for s in slots)


def next_opening(slots: list[TimeSlot], moment: datetime) -> datetime | None:
    """Próximo inicio de franja (en hora de La Habana) dentro de la semana siguiente."""
    local = moment.astimezone(HAVANA)
    best: datetime | None = None
    for offset in range(8):
        day = (local + timedelta(days=offset)).date()
        for s in slots:
            if s.weekday != day.weekday():
                continue
            start = datetime.combine(day, s.start, tzinfo=HAVANA)
            if start > local and (best is None or start < best):
                best = start
    return best


def daily_hours(slots: list[TimeSlot]) -> list[float]:
    """Horas cubiertas por día (lunes..domingo), uniendo franjas solapadas."""
    hours = []
    for day in range(7):
        intervals = sorted((s.start, s.end) for s in slots if s.weekday == day)
        total, cur_start, cur_end = 0.0, None, None
        for start, end in intervals:
            if cur_end is None or start > cur_end:
                if cur_end is not None:
                    total += TimeSlot(day, cur_start, cur_end).hours  # type: ignore[arg-type]
                cur_start, cur_end = start, end
            else:
                cur_end = max(cur_end, end)
        if cur_end is not None:
            total += TimeSlot(day, cur_start, cur_end).hours  # type: ignore[arg-type]
        hours.append(total)
    return hours


@dataclass(frozen=True, slots=True)
class HelplineConfig:
    phone: str
    label: str
    off_hours_message: str
    emergency_phone: str | None
    slots: list[TimeSlot] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Professional:
    id: UUID
    full_name: str
    specialty: str
    phone: str
    sort_order: int = 0
    is_active: bool = True
    slots: list[TimeSlot] = field(default_factory=list)


DEFAULT_CONFIG = HelplineConfig(
    phone="+53 7 000 0000",
    label="Teléfono de atención al paciente y su familia",
    off_hours_message=(
        "Fuera de horario. Si la situación es urgente, acude al cuerpo de guardia del hospital "
        "o llama al número de urgencias."
    ),
    emergency_phone="+53 7 000 0001",
    slots=[TimeSlot(d, time(8), time(16)) for d in range(5)] + [TimeSlot(d, time(9), time(15)) for d in (5, 6)],
)


class HelplineRepository(Protocol):
    async def get_config(self) -> HelplineConfig | None: ...
    async def save_config(self, config: HelplineConfig) -> HelplineConfig: ...
    async def list_professionals(self, *, active_only: bool) -> list[Professional]: ...
    async def get_professional(self, professional_id: UUID) -> Professional | None: ...
    async def add_professional(self, data: dict[str, object]) -> Professional: ...
    async def update_professional(self, professional_id: UUID, changes: dict[str, object]) -> Professional | None: ...
    async def delete_professional(self, professional_id: UUID) -> bool: ...
