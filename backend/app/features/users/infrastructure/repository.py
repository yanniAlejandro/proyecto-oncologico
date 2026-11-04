from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.domain.model import NewUser, User
from app.features.users.infrastructure.orm import UserRow


def to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        role=row.role,
        password_hash=row.password_hash,
        is_active=row.is_active,
        created_at=row.created_at,
    )


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: UUID) -> User | None:
        row = await self._s.get(UserRow, user_id)
        return to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        row = (
            await self._s.execute(select(UserRow).where(func.lower(UserRow.email) == email.lower()))
        ).scalar_one_or_none()
        return to_domain(row) if row else None

    async def list_all(self) -> list[User]:
        rows = (await self._s.execute(select(UserRow).order_by(UserRow.full_name))).scalars().all()
        return [to_domain(r) for r in rows]

    async def add(self, new: NewUser) -> User:
        row = UserRow(email=new.email, full_name=new.full_name, role=new.role, password_hash=new.password_hash)
        self._s.add(row)
        await self._s.commit()
        await self._s.refresh(row)
        return to_domain(row)

    async def set_active(self, user_id: UUID, active: bool) -> None:
        await self._s.execute(update(UserRow).where(UserRow.id == user_id).values(is_active=active))
        await self._s.commit()
