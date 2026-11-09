from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.application.use_cases import CreateUser, DeactivateUser, ListUsers, UpdateUser
from app.features.users.domain.ports import PasswordHasher, UserRepository
from app.features.users.infrastructure.repository import SqlUserRepository
from app.shared.infrastructure.database import get_session
from app.shared.infrastructure.security import BcryptPasswordHasher


def get_user_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return SqlUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


Users = Annotated[UserRepository, Depends(get_user_repository)]
Hasher = Annotated[PasswordHasher, Depends(get_password_hasher)]


def list_users(users: Users) -> ListUsers:
    return ListUsers(users)


def create_user(users: Users, hasher: Hasher) -> CreateUser:
    return CreateUser(users, hasher)


def update_user(users: Users, hasher: Hasher) -> UpdateUser:
    return UpdateUser(users, hasher)


def deactivate_user(users: Users, hasher: Hasher) -> DeactivateUser:
    return DeactivateUser(users, hasher)
