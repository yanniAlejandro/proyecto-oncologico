"""documentos: archivo almacenado (storage_key, size_bytes) y file_url opcional

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("storage_key", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("size_bytes", sa.BigInteger(), nullable=True))
    op.create_unique_constraint("uq_documents_storage_key", "documents", ["storage_key"])
    op.alter_column("documents", "file_url", existing_type=sa.String(length=1000), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE documents SET file_url = '' WHERE file_url IS NULL")
    op.alter_column("documents", "file_url", existing_type=sa.String(length=1000), nullable=False)
    op.drop_constraint("uq_documents_storage_key", "documents", type_="unique")
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "storage_key")
