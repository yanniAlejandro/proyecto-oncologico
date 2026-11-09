from pydantic import BaseModel, EmailStr, Field

from app.features.users.domain.model import User
from app.shared.domain.actor import Role, Section


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    role: Role = Role.MEDICO
    permissions: list[Section] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2)
    role: Role | None = None
    is_active: bool | None = None
    permissions: list[Section] | None = None
    password: str | None = Field(None, min_length=6)


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: list[str]

    @classmethod
    def of(cls, u: User) -> "UserOut":
        return cls(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_active=u.is_active,
            permissions=sorted(s.value for s in u.permissions),
        )
