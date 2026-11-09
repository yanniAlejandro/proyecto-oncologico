from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.helpline.domain.model import HelplineConfig, Professional, TimeSlot, parse_slot, slot_to_json
from app.features.helpline.infrastructure.orm import HelplineConfigRow, HelplineProfessionalRow


def _slots(raw: list[dict[str, object]]) -> list[TimeSlot]:
    return [s for s in (parse_slot(r) for r in raw or []) if s is not None]


def _pro(row: HelplineProfessionalRow) -> Professional:
    return Professional(
        id=row.id,
        full_name=row.full_name,
        specialty=row.specialty,
        phone=row.phone,
        sort_order=row.sort_order,
        is_active=row.is_active,
        slots=_slots(row.slots),
    )


class SqlHelplineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_config(self) -> HelplineConfig | None:
        row = await self._s.get(HelplineConfigRow, 1, populate_existing=True)
        if row is None:
            return None
        return HelplineConfig(
            phone=row.phone,
            label=row.label,
            off_hours_message=row.off_hours_message,
            emergency_phone=row.emergency_phone,
            slots=_slots(row.slots),
        )

    async def save_config(self, config: HelplineConfig) -> HelplineConfig:
        row = await self._s.get(HelplineConfigRow, 1) or HelplineConfigRow(id=1)
        row.phone = config.phone
        row.label = config.label
        row.off_hours_message = config.off_hours_message
        row.emergency_phone = config.emergency_phone
        row.slots = [slot_to_json(s) for s in config.slots]
        self._s.add(row)
        await self._s.commit()
        saved = await self.get_config()
        assert saved is not None
        return saved

    async def list_professionals(self, *, active_only: bool) -> list[Professional]:
        q = select(HelplineProfessionalRow).order_by(
            HelplineProfessionalRow.sort_order, HelplineProfessionalRow.full_name
        )
        if active_only:
            q = q.where(HelplineProfessionalRow.is_active.is_(True))
        return [_pro(r) for r in (await self._s.execute(q)).scalars().all()]

    async def get_professional(self, professional_id: UUID) -> Professional | None:
        row = await self._s.get(HelplineProfessionalRow, professional_id, populate_existing=True)
        return _pro(row) if row else None

    async def add_professional(self, data: dict[str, object]) -> Professional:
        values = dict(data)
        values["slots"] = [slot_to_json(s) for s in values.get("slots", [])]  # type: ignore[attr-defined]
        row = HelplineProfessionalRow(**values)
        self._s.add(row)
        await self._s.commit()
        professional_id = row.id
        saved = await self.get_professional(professional_id)
        assert saved is not None
        return saved

    async def update_professional(self, professional_id: UUID, changes: dict[str, object]) -> Professional | None:
        row = await self._s.get(HelplineProfessionalRow, professional_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, [slot_to_json(s) for s in value] if key == "slots" else value)  # type: ignore[attr-defined]
        await self._s.commit()
        return await self.get_professional(professional_id)

    async def delete_professional(self, professional_id: UUID) -> bool:
        result = await self._s.execute(
            delete(HelplineProfessionalRow).where(HelplineProfessionalRow.id == professional_id)
        )
        await self._s.commit()
        return bool(result.rowcount)
