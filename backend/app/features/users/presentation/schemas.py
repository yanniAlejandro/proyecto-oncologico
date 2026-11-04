from pydantic import BaseModel, EmailStr, Field

from app.features.users.domain.model import User
from app.shared.domain.actor import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    role: Role = Role.MEDICO


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    @classmethod
    def of(cls, u: User) -> "UserOut":
        return cls(id=str(u.id), email=u.email, full_name=u.full_name, role=u.role.value, is_active=u.is_active)
