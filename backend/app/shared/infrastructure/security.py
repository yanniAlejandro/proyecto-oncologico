"""Adaptadores de seguridad: hash de contraseñas (bcrypt) y tokens (JWT)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.shared.infrastructure.config import settings


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except ValueError:
            return False


class JwtTokenService:
    def __init__(
        self,
        secret: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
        expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire = timedelta(minutes=expire_minutes)

    def issue(self, user_id: UUID, role: str) -> str:
        payload = {"sub": str(user_id), "role": role, "exp": datetime.now(UTC) + self._expire}
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def subject(self, token: str) -> UUID | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return UUID(payload["sub"])
        except (JWTError, KeyError, ValueError, TypeError):
            return None
