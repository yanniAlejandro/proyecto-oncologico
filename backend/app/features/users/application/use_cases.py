from uuid import UUID

from app.features.users.domain.model import NewUser, User, normalize_email
from app.features.users.domain.ports import PasswordHasher, UserRepository
from app.shared.domain.actor import ADMINS, Actor, Role, require
from app.shared.domain.result import AppError, Err, Ok, Result

MIN_PASSWORD_LENGTH = 6


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def __call__(self, actor: Actor | None) -> Result[list[User]]:
        if isinstance(auth := require(actor, ADMINS), Err):
            return auth
        return Ok(await self._users.list_all())


class CreateDoctor:
    """El administrador solo da de alta cuentas de médico."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def __call__(
        self, actor: Actor | None, *, email: str, password: str, full_name: str, role: Role = Role.MEDICO
    ) -> Result[User]:
        if isinstance(auth := require(actor, ADMINS), Err):
            return auth
        if role != Role.MEDICO:
            return Err(AppError.invalid("Solo se pueden crear cuentas de médico"))
        if len(password) < MIN_PASSWORD_LENGTH:
            return Err(AppError.invalid(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"))
        email = normalize_email(email)
        if await self._users.get_by_email(email) is not None:
            return Err(AppError.conflict("El correo ya está registrado"))
        user = await self._users.add(
            NewUser(
                email=email, full_name=full_name.strip(), role=Role.MEDICO, password_hash=self._hasher.hash(password)
            )
        )
        return Ok(user)


class DeactivateUser:
    """Desactiva (no borra) cuentas de médico. No se puede desactivar a uno mismo."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def __call__(self, actor: Actor | None, user_id: UUID) -> Result[None]:
        if isinstance(auth := require(actor, ADMINS), Err):
            return auth
        user = await self._users.get(user_id)
        if user is None:
            return Err(AppError.not_found("Usuario no encontrado"))
        if user.id == auth.value.id:
            return Err(AppError.invalid("No puedes desactivar tu propia cuenta"))
        if user.role != Role.MEDICO:
            return Err(AppError.invalid("Solo se pueden desactivar cuentas de médico"))
        await self._users.set_active(user_id, False)
        return Ok(None)
