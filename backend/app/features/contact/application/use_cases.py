from app.features.contact.domain.model import EDITABLE_FIELDS, ContactInfo, ContactRepository
from app.shared.domain.actor import Actor, require_admin
from app.shared.domain.result import AppError, Err, Ok, Result


class GetContact:
    def __init__(self, contact: ContactRepository) -> None:
        self._contact = contact

    async def __call__(self) -> Result[ContactInfo]:
        info = await self._contact.get()
        return Ok(info) if info else Err(AppError.not_found("Información de contacto no configurada"))


class UpdateContact:
    def __init__(self, contact: ContactRepository) -> None:
        self._contact = contact

    async def __call__(self, actor: Actor | None, changes: dict[str, object]) -> Result[ContactInfo]:
        if isinstance(auth := require_admin(actor), Err):
            return auth
        return Ok(await self._contact.upsert({k: v for k, v in changes.items() if k in EDITABLE_FIELDS}))
