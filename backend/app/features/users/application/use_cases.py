"""Gestión de cuentas: solo administradores.

Salvaguardas: nadie se desactiva ni se quita el rol de administrador a sí mismo,
y siempre queda al menos un administrador activo.
"""

from uuid import UUID

from app.features.users.domain.model import NewUser, User, UserChanges, normalize_email
from app.features.users.domain.ports import PasswordHasher, UserRepository
from app.shared.domain.actor import Actor, Role, Section, require_admin
from app.shared.domain.result import AppError, Err, Ok, Result

MIN_PASSWORD_LENGTH = 6
NOT_FOUND = "Usuario no encontrado"
LAST_ADMIN = "Debe quedar al menos un administrador activo"


def _password_error(password: str) -> Err | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return Err(AppError.invalid(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"))
    return None


def _clean_permissions(role: Role, permissions: frozenset[Section]) -> frozenset[Section]:
    """El admin las tiene todas implícitamente: no se guardan."""
    return frozenset() if role is Role.ADMINISTRADOR else permissions


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def __call__(self, actor: Actor | None) -> Result[list[User]]:
        if isinstance(auth := require_admin(actor), Err):
            return auth
        return Ok(await self._users.list_all())


class CreateUser:
    """Alta de médicos (sin permisos salvo que se indiquen) o de administradores."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def __call__(
        self,
        actor: Actor | None,
        *,
        email: str,
        password: str,
        full_name: str,
        role: Role = Role.MEDICO,
        permissions: frozenset[Section] = frozenset(),
    ) -> Result[User]:
        if isinstance(auth := require_admin(actor), Err):
            return auth
        if bad := _password_error(password):
            return bad
        full_name = full_name.strip()
        if len(full_name) < 2:
            return Err(AppError.invalid("El nombre debe tener al menos 2 caracteres"))
        email = normalize_email(email)
        if await self._users.get_by_email(email) is not None:
            return Err(AppError.conflict("El correo ya está registrado"))
        user = await self._users.add(
            NewUser(
                email=email,
                full_name=full_name,
                role=role,
                password_hash=self._hasher.hash(password),
                permissions=_clean_permissions(role, permissions),
            )
        )
        return Ok(user)


class UpdateUser:
    """Nombre, rol, permisos, estado activo y (opcional) nueva contraseña."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def __call__(
        self,
        actor: Actor | None,
        user_id: UUID,
        *,
        full_name: str | None = None,
        role: Role | None = None,
        is_active: bool | None = None,
        permissions: frozenset[Section] | None = None,
        password: str | None = None,
    ) -> Result[User]:
        if isinstance(auth := require_admin(actor), Err):
            return auth
        user = await self._users.get(user_id)
        if user is None:
            return Err(AppError.not_found(NOT_FOUND))

        is_self = user.id == auth.value.id
        loses_admin = (
            user.role is Role.ADMINISTRADOR
            and user.is_active
            and ((role is not None and role is not Role.ADMINISTRADOR) or is_active is False)
        )
        if is_self and is_active is False:
            return Err(AppError.invalid("No puedes desactivar tu propia cuenta"))
        if is_self and loses_admin:
            return Err(AppError.invalid("No puedes quitarte el rol de administrador"))
        if loses_admin and await self._users.count_active_admins() <= 1:
            return Err(AppError.invalid(LAST_ADMIN))

        if full_name is not None and len(full_name.strip()) < 2:
            return Err(AppError.invalid("El nombre debe tener al menos 2 caracteres"))
        if password is not None and (bad := _password_error(password)):
            return bad

        final_role = role or user.role
        if permissions is None and final_role is Role.ADMINISTRADOR and user.role is not Role.ADMINISTRADOR:
            permissions = frozenset()  # al ascender, se limpian los permisos sueltos
        changes = UserChanges(
            full_name=full_name.strip() if full_name is not None else None,
            role=role,
            is_active=is_active,
            permissions=_clean_permissions(final_role, permissions) if permissions is not None else None,
            password_hash=self._hasher.hash(password) if password is not None else None,
        )
        updated = await self._users.update(user_id, changes)
        return Ok(updated) if updated else Err(AppError.not_found(NOT_FOUND))


class DeactivateUser:
    """Atajo de ``UpdateUser(is_active=False)`` (DELETE /users/{id}): desactiva, no borra."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._update = UpdateUser(users, hasher)

    async def __call__(self, actor: Actor | None, user_id: UUID) -> Result[None]:
        result = await self._update(actor, user_id, is_active=False)
        return result if isinstance(result, Err) else Ok(None)
