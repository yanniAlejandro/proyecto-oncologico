"""publicaciones (enlace + imagen almacenada) sustituyen a las noticias

Revision ID: 0004
Revises: 0003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "publications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_key", sa.String(length=100), nullable=True),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_key"),
    )
    op.create_index(op.f("ix_publications_created_at"), "publications", ["created_at"], unique=False)
    # Acordado: no se migran las noticias (solo había una de prueba).
    op.drop_index(op.f("ix_news_is_published"), table_name="news", if_exists=True)
    op.drop_index(op.f("ix_news_created_at"), table_name="news", if_exists=True)
    op.drop_table("news")


def downgrade() -> None:
    op.create_table(
        "news",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_news_created_at"), "news", ["created_at"], unique=False)
    op.create_index(op.f("ix_news_is_published"), "news", ["is_published"], unique=False)
    op.drop_index(op.f("ix_publications_created_at"), table_name="publications")
    op.drop_table("publications")
