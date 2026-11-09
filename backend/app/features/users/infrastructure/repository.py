from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.domain.model import NewUser, User, UserChanges
from app.features.users.infrastructure.orm import UserPermissionRow, UserRow
from app.shared.domain.actor import Role, normalize_permissions


def to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        role=row.role,
        password_hash=row.password_hash,
        is_active=row.is_active,
        created_at=row.created_at,
        permissions=normalize_permissions(p.section for p in row.permission_rows),
    )


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _load(self, user_id: UUID) -> UserRow | None:
        # populate_existing: relee de la BD aunque la fila esté en la identity map (permisos recién cambiados).
        stmt = select(UserRow).where(UserRow.id == user_id).execution_options(populate_existing=True)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get(self, user_id: UUID) -> User | None:
        row = await self._load(user_id)
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
        row.permission_rows = [UserPermissionRow(section=s.value) for s in sorted(new.permissions)]
        self._s.add(row)
        await self._s.commit()
        user_id = row.id
        loaded = await self._load(user_id)
        assert loaded is not None
        return to_domain(loaded)

    async def update(self, user_id: UUID, changes: UserChanges) -> User | None:
        row = await self._load(user_id)
        if row is None:
            return None
        if changes.full_name is not None:
            row.full_name = changes.full_name
        if changes.role is not None:
            row.role = changes.role
        if changes.is_active is not None:
            row.is_active = changes.is_active
        if changes.password_hash is not None:
            row.password_hash = changes.password_hash
        if changes.permissions is not None:
            row.permission_rows = [UserPermissionRow(section=s.value) for s in sorted(changes.permissions)]
        await self._s.commit()
        loaded = await self._load(user_id)
        return to_domain(loaded) if loaded else None

    async def count_active_admins(self) -> int:
        stmt = select(func.count()).where(UserRow.role == Role.ADMINISTRADOR, UserRow.is_active.is_(True))
        return int((await self._s.execute(stmt)).scalar_one())
