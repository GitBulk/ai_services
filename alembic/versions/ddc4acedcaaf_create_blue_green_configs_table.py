"""create_blue_green_configs_table

Revision ID: ddc4acedcaaf
Revises:
Create Date: 2026-03-26 13:08:37.787016

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ddc4acedcaaf"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# raw sql
# def upgrade():
#     # 1. Tạo bảng bằng SQL thuần (đảm bảo đúng kiểu dữ liệu Postgres 9.5)
#     op.execute("""
#         CREATE TABLE blue_green_configs (
#             id SERIAL PRIMARY KEY,
#             key VARCHAR NOT NULL,
#             value VARCHAR NOT NULL,
#             last_computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#     """)

#     # 2. Tạo Unique Index (để tránh duplicate key config)
#     op.execute("""
#         CREATE UNIQUE INDEX idx_blue_green_configs_key_unique
#         ON blue_green_configs (key);
#     """)

#     # 3. Insert dữ liệu khởi tạo bằng Raw SQL
#     op.execute("""
#         INSERT INTO blue_green_configs (key, value, last_computed_at)
#         VALUES ('nova_ai_deployment_current_color', 'blue', NOW());
#     """)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "blue_green_configs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("last_computed_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index("ix_blue_green_configs_on_key_unique", "blue_green_configs", ["key"], unique=True)

    # seed data
    op.execute("""
        INSERT INTO blue_green_configs (key, value, last_computed_at) 
        VALUES ('nova_ai_deployment_current_color', 'blue', NOW());
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # dangerous
    # op.drop_table('blue_green_configs')
    pass
