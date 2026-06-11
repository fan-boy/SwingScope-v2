"""add risk_amount to trade_plans

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trade_plans", sa.Column("risk_amount", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("trade_plans", "risk_amount")
