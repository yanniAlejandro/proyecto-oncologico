"""permisos por sección para médicos; se elimina el rol encargado

Revision ID: 0003
Revises: 0002
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("section", sa.String(length=40), primary_key=True),
    )
    # Las cuentas de encargado se eliminan; su autoría queda en NULL (las FK son ON DELETE SET NULL).
    op.execute("DELETE FROM users WHERE role = 'encargado'")
    # PostgreSQL no permite quitar un valor de un ENUM: se crea el tipo nuevo y se migra la columna.
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('administrador', 'medico')")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")


def downgrade() -> None:
    op.execute("ALTER TYPE user_role RENAME TO user_role_new")
    op.execute("CREATE TYPE user_role AS ENUM ('administrador', 'encargado', 'medico')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_new")
    op.drop_table("user_permissions")
