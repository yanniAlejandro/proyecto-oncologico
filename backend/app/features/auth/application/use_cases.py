from app.features.auth.domain.ports import TokenService
from app.features.users.domain.model import normalize_email
from app.features.users.domain.ports import PasswordHasher, UserRepository
from app.shared.domain.actor import Actor
from app.shared.domain.result import AppError, Err, Ok, Result

INVALID_CREDENTIALS = "Credenciales inválidas"


class Login:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def __call__(self, email: str, password: str) -> Result[str]:
        user = await self._users.get_by_email(normalize_email(email))
        # Mismo mensaje para usuario inexistente, inactivo o contraseña errónea.
        if user is None or not user.is_active or not self._hasher.verify(password, user.password_hash):
            return Err(AppError.unauthenticated(INVALID_CREDENTIALS))
        return Ok(self._tokens.issue(user.id, user.role.value))


class ResolveActor:
    """Token → Actor activo, o ``None`` para visitante/token inválido."""

    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def __call__(self, token: str | None) -> Actor | None:
        if not token:
            return None
        user_id = self._tokens.subject(token)
        if user_id is None:
            return None
        user = await self._users.get(user_id)
        if user is None or not user.is_active:
            return None
        return Actor(id=user.id, role=user.role, full_name=user.full_name)
