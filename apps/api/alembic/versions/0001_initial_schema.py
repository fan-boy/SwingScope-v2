"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # watchlists
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])

    # watchlist_items
    op.create_table(
        "watchlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("alert_price", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])
    op.create_index("ix_watchlist_items_symbol", "watchlist_items", ["symbol"])

    # scan_runs
    op.create_table(
        "scan_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="RUNNING"),
        sa.Column("market_regime", sa.String(20), nullable=True),
        sa.Column("tickers_scanned", sa.Integer, nullable=False, default=0),
        sa.Column("candidates_found", sa.Integer, nullable=False, default=0),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("is_mocked", sa.Boolean, nullable=False, default=False),
        sa.Column("meta", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scan_runs_run_date", "scan_runs", ["run_date"])

    # scan_candidates
    op.create_table(
        "scan_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_date", sa.Date, nullable=False),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("technical_score", sa.Float, nullable=False, default=0),
        sa.Column("sentiment_score", sa.Float, nullable=False, default=0),
        sa.Column("regime_modifier", sa.Float, nullable=False, default=0),
        sa.Column("squeeze_score", sa.Float, nullable=True),
        sa.Column("confidence", sa.String(10), nullable=False),
        sa.Column("entry", sa.Float, nullable=False),
        sa.Column("stop", sa.Float, nullable=False),
        sa.Column("target1", sa.Float, nullable=False),
        sa.Column("target2", sa.Float, nullable=True),
        sa.Column("rr_ratio", sa.Float, nullable=False),
        sa.Column("atr14", sa.Float, nullable=True),
        sa.Column("direction", sa.String(5), nullable=False, default="LONG"),
        sa.Column("strategy", sa.String(50), nullable=True),
        sa.Column("regime", sa.String(20), nullable=True),
        sa.Column("thesis", sa.Text, nullable=True),
        sa.Column("technical_setup", sa.Text, nullable=True),
        sa.Column("catalyst_summary", sa.Text, nullable=True),
        sa.Column("invalidation", sa.Text, nullable=True),
        sa.Column("generated_by_llm", sa.Boolean, nullable=False, default=False),
        sa.Column("status", sa.String(20), nullable=False, default="NEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scan_candidates_run_symbol", "scan_candidates", ["scan_run_id", "symbol"])
    op.create_index("ix_scan_candidates_symbol_date", "scan_candidates", ["symbol", "run_date"])
    op.create_index("ix_scan_candidates_score", "scan_candidates", ["score"])
    op.create_index("ix_scan_candidates_status", "scan_candidates", ["status"])

    # positions
    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, default="OPEN"),
        sa.Column("direction", sa.String(5), nullable=False, default="LONG"),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("avg_entry_price", sa.Float, nullable=False),
        sa.Column("stop_price", sa.Float, nullable=True),
        sa.Column("target_price", sa.Float, nullable=True),
        sa.Column("avg_exit_price", sa.Float, nullable=True),
        sa.Column("realized_pnl", sa.Float, nullable=True),
        sa.Column("opened_at", sa.Date, nullable=False),
        sa.Column("closed_at", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_positions_symbol_status", "positions", ["symbol", "status"])
    op.create_index("ix_positions_opened_at", "positions", ["opened_at"])

    # trade_plans
    op.create_table(
        "trade_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scan_candidates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False, default="LONG"),
        sa.Column("status", sa.String(20), nullable=False, default="DRAFT"),
        sa.Column("entry", sa.Float, nullable=False),
        sa.Column("stop", sa.Float, nullable=False),
        sa.Column("target1", sa.Float, nullable=False),
        sa.Column("target2", sa.Float, nullable=True),
        sa.Column("quantity", sa.Float, nullable=True),
        sa.Column("rr_ratio", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_plans_user_id", "trade_plans", ["user_id"])
    op.create_index("ix_trade_plans_status", "trade_plans", ["status"])
    op.create_index("ix_trade_plans_symbol", "trade_plans", ["symbol"])

    # trade_orders
    op.create_table(
        "trade_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trade_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("positions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("order_type", sa.String(20), nullable=False),
        sa.Column("side", sa.String(5), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("limit_price", sa.Float, nullable=True),
        sa.Column("stop_price", sa.Float, nullable=True),
        sa.Column("filled_price", sa.Float, nullable=True),
        sa.Column("filled_quantity", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="PENDING"),
        sa.Column("broker_order_id", sa.String(100), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_response", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_orders_plan_id", "trade_orders", ["plan_id"])
    op.create_index("ix_trade_orders_status", "trade_orders", ["status"])
    op.create_index("ix_trade_orders_symbol", "trade_orders", ["symbol"])

    # execution_logs
    op.create_table(
        "execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("level", sa.String(10), nullable=False, default="INFO"),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meta", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_execution_logs_entity", "execution_logs", ["entity_type", "entity_id"])
    op.create_index("ix_execution_logs_level", "execution_logs", ["level"])
    op.create_index("ix_execution_logs_created_at", "execution_logs", ["created_at"])

    # app_settings
    op.create_table(
        "app_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("min_score", sa.Float, nullable=False, default=55.0),
        sa.Column("min_rr", sa.Float, nullable=False, default=2.0),
        sa.Column("max_candidates", sa.Integer, nullable=False, default=10),
        sa.Column("mock_mode", sa.Boolean, nullable=False, default=False),
        sa.Column("notify_on_scan", sa.Boolean, nullable=False, default=True),
        sa.Column("notify_on_fill", sa.Boolean, nullable=False, default=True),
        sa.Column("telegram_chat_id", sa.String(50), nullable=True),
        sa.Column("extra", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_app_settings_user"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("execution_logs")
    op.drop_table("trade_orders")
    op.drop_table("trade_plans")
    op.drop_table("positions")
    op.drop_table("scan_candidates")
    op.drop_table("scan_runs")
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_table("users")
