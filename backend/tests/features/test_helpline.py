from datetime import UTC, datetime, time
from uuid import uuid4

from app.features.helpline.application import use_cases as uc
from app.features.helpline.domain.model import (
    DEFAULT_CONFIG,
    HAVANA,
    MIN_DAILY_HOURS,
    TimeSlot,
    daily_hours,
    is_available,
    next_opening,
    parse_slot,
)
from app.shared.domain.result import ErrorKind
from tests.fakes import DOCTOR, EDITOR, FakeHelpline
from tests.helpers import err, ok

MON_8_16 = TimeSlot(0, time(8), time(16))


def havana(y, m, d, hh, mm=0) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=HAVANA)


def test_parse_slot_validates_day_and_order():
    assert parse_slot({"weekday": 0, "start": "08:00", "end": "16:00"}) == MON_8_16
    assert parse_slot({"weekday": 7, "start": "08:00", "end": "16:00"}) is None
    assert parse_slot({"weekday": 0, "start": "16:00", "end": "08:00"}) is None
    assert parse_slot({"weekday": 0, "start": "8h"}) is None


def test_availability_uses_havana_time_regardless_of_server_timezone():
    monday_9_havana = havana(2026, 11, 9, 9)  # 9 nov 2026 es lunes
    assert is_available([MON_8_16], monday_9_havana)
    assert is_available([MON_8_16], monday_9_havana.astimezone(UTC))  # mismo instante en UTC
    assert not is_available([MON_8_16], havana(2026, 11, 9, 16))  # fin excluido
    assert not is_available([MON_8_16], havana(2026, 11, 10, 9))  # martes


def test_next_opening_wraps_to_next_week():
    assert next_opening([MON_8_16], havana(2026, 11, 9, 7)) == havana(2026, 11, 9, 8)
    assert next_opening([MON_8_16], havana(2026, 11, 9, 17)) == havana(2026, 11, 16, 8)
    assert next_opening([], havana(2026, 11, 9, 7)) is None


def test_daily_hours_merges_overlaps_and_default_meets_six_hour_standard():
    slots = [TimeSlot(0, time(8), time(12)), TimeSlot(0, time(11), time(14)), TimeSlot(0, time(15), time(16))]
    assert daily_hours(slots)[0] == 7.0
    assert all(h >= MIN_DAILY_HOURS for h in daily_hours(DEFAULT_CONFIG.slots))


async def test_get_helpline_defaults_and_marks_each_professional():
    repo = FakeHelpline()
    ok(
        await uc.CreateProfessional(repo)(
            EDITOR, {"full_name": "Dra. Ana", "specialty": "Pediatría", "phone": "+53 7 111 1111", "slots": [MON_8_16]}
        )
    )
    ok(
        await uc.CreateProfessional(repo)(
            EDITOR, {"full_name": "Dr. Luis", "specialty": "Psicología", "phone": "7-222-2222", "is_active": False}
        )
    )
    view = await uc.GetHelpline(repo)(havana(2026, 11, 9, 9))
    assert view.config == DEFAULT_CONFIG and view.status.available_now
    assert [(p.full_name, s.available_now) for p, s in view.professionals] == [("Dra. Ana", True)]  # inactivo oculto
    later = await uc.GetHelpline(repo)(havana(2026, 11, 9, 20))
    assert not later.status.available_now and later.status.next_opening == havana(2026, 11, 10, 8)


async def test_update_config_requires_permission_and_validates():
    repo = FakeHelpline()
    update = uc.UpdateHelplineConfig(repo)
    saved = ok(await update(EDITOR, {"phone": "+53 7 649 0000", "emergency_phone": "", "slots": [MON_8_16]}))
    assert saved.phone == "+53 7 649 0000" and saved.emergency_phone is None and saved.slots == [MON_8_16]
    assert saved.label == DEFAULT_CONFIG.label  # lo no enviado se conserva
    err(await update(EDITOR, {"phone": "llámanos"}), ErrorKind.INVALID)
    err(await update(EDITOR, {"off_hours_message": "  "}), ErrorKind.INVALID)
    err(await update(DOCTOR, {"phone": "+53 7 649 0000"}), ErrorKind.FORBIDDEN)


async def test_professionals_crud_and_management_list_includes_inactive():
    repo = FakeHelpline()
    pro = ok(
        await uc.CreateProfessional(repo)(
            EDITOR, {"full_name": " Dra. Ana ", "specialty": "Pediatría", "phone": "+53 5 123 4567"}
        )
    )
    assert pro.full_name == "Dra. Ana" and pro.slots == []
    err(
        await uc.CreateProfessional(repo)(
            EDITOR, {"full_name": "X", "specialty": "Pediatría", "phone": "+53 5 123 4567"}
        ),
        ErrorKind.INVALID,
    )
    err(
        await uc.CreateProfessional(repo)(EDITOR, {"full_name": "Dra. B", "specialty": "Pediatría", "phone": "123"}),
        ErrorKind.INVALID,
    )
    hidden = ok(await uc.UpdateProfessional(repo)(EDITOR, pro.id, {"is_active": False}))
    assert not hidden.is_active
    assert len(ok(await uc.ListProfessionalsForManagement(repo)(EDITOR))) == 1
    err(await uc.ListProfessionalsForManagement(repo)(DOCTOR), ErrorKind.FORBIDDEN)
    err(await uc.UpdateProfessional(repo)(EDITOR, uuid4(), {"phone": "+53 5 123 4567"}), ErrorKind.NOT_FOUND)
    ok(await uc.DeleteProfessional(repo)(EDITOR, pro.id))
    err(await uc.DeleteProfessional(repo)(EDITOR, pro.id), ErrorKind.NOT_FOUND)
