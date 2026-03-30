"""create_scoring_profiles_table

Revision ID: 1a7f9e640352
Revises: ddc4acedcaaf
Create Date: 2026-03-29 19:48:19.421034

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a7f9e640352"
down_revision: str | Sequence[str] | None = "ddc4acedcaaf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    # 1. Tạo bảng scoring_profiles
    op.create_table(
        "scoring_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="draft", nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("active_slot", sa.Integer(), nullable=True),
        sa.Column("parent_profile_id", sa.Integer(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_profile_id"], ["scoring_profiles.id"], name="fk_scoring_profiles_parent"),
        sa.PrimaryKeyConstraint("id"),
    )

    # op.create_index(
    #     "index_uniq_scoring_profile_on_name",
    #     "scoring_profiles",
    #     ["name"],
    #     unique=True,
    # )
    # op.create_index(
    #     "index_uniq_scoring_profile_on_active_slot",
    #     "scoring_profiles",
    #     ["active_slot"],
    #     unique=True,
    # )

    # # Tạo Check Constraint: Giới hạn giá trị slot (1 hoặc 2)
    # op.create_check_constraint(
    #     "ck_scoring_profiles_valid_slot", "scoring_profiles", "active_slot IS NULL OR active_slot IN (1, 2)"
    # )

    # # Tạo Check Constraint: Nhất quán giữa Status và Slot
    # # Chú ý: SQL so sánh String có phân biệt hoa thường
    # op.create_check_constraint(
    #     "ck_scoring_profiles_status_slot_consistency",
    #     "scoring_profiles",
    #     "(status = 'active' AND active_slot IN (1, 2)) OR (status != 'active' AND active_slot IS NULL)",
    # )

    # hoặc dùng raw sql tạo index, contraint
    op.execute("""
        -- Unique cho Name
        CREATE UNIQUE INDEX uq_scoring_profiles_name ON scoring_profiles (name);

        -- Unique cho Slot (Chống Race Condition)
        CREATE UNIQUE INDEX uq_scoring_profiles_active_slot ON scoring_profiles (active_slot);

        -- Check Slot ID (1 hoặc 2 hoặc is null)
        ALTER TABLE scoring_profiles
        ADD CONSTRAINT ck_scoring_profiles_valid_slot
        CHECK (active_slot IN (1, 2) OR active_slot IS NULL);

        -- Check Logic Status & Slot Sync
        ALTER TABLE scoring_profiles
        ADD CONSTRAINT ck_scoring_profiles_status_slot_consistency
        CHECK (
            (status = 'active' AND active_slot IN (1, 2)) OR
            (status != 'active' AND active_slot IS NULL)
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
