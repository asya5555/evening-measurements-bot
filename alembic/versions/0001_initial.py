"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255)),
        sa.Column("first_name", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"])

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("first_reminder_time", sa.String(length=5), nullable=False),
        sa.Column("second_reminder_time", sa.String(length=5), nullable=False),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False),
        sa.Column("required_sections", postgresql.JSONB(), nullable=False),
        sa.Column("daily_analytics_enabled", sa.Boolean(), nullable=False),
        sa.Column("weekly_report_enabled", sa.Boolean(), nullable=False),
        sa.Column("monthly_report_enabled", sa.Boolean(), nullable=False),
        sa.Column("mood_scale", sa.String(length=32), nullable=False),
        sa.Column("tracked_measurements", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "daily_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("structured_data", postgresql.JSONB(), nullable=False),
        sa.Column("extraction_result", postgresql.JSONB(), nullable=False),
        sa.Column("prompt_version", sa.String(length=64)),
        sa.Column("model_id", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("user_id", "observed_on", name="uq_daily_entries_user_date"),
    )
    op.create_index("ix_daily_entries_user_id", "daily_entries", ["user_id"])
    op.create_index("ix_daily_entries_observed_on", "daily_entries", ["observed_on"])

    op.create_table(
        "entry_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("daily_entries.id", ondelete="CASCADE")),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_reason", sa.String(length=128), nullable=False),
        sa.Column("data_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_entry_versions_entry_id", "entry_versions", ["entry_id"])

    op.create_table(
        "raw_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("daily_entries.id", ondelete="SET NULL")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger()),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redacted_text", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_raw_messages_user_id", "raw_messages", ["user_id"])

    op.create_table(
        "media_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("daily_entries.id", ondelete="SET NULL")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("local_path", sa.Text()),
        sa.Column("transcription", sa.Text()),
        sa.Column("analysis", postgresql.JSONB(), nullable=False),
        sa.Column("purge_after", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_files_user_id", "media_files", ["user_id"])

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("user_id", "observed_on", "kind", name="uq_reminder_once"),
    )
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"])
    op.create_index("ix_reminders_scheduled_for", "reminders", ["scheduled_for"])

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("report_text", sa.Text(), nullable=False),
        sa.Column("report_data", postgresql.JSONB(), nullable=False),
        sa.Column("model_id", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "period", "starts_on", "ends_on", name="uq_report_period"),
    )
    op.create_index("ix_generated_reports_user_id", "generated_reports", ["user_id"])

    op.create_table(
        "processed_updates",
        sa.Column("update_id", sa.BigInteger(), primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("processed_updates")
    op.drop_table("generated_reports")
    op.drop_table("reminders")
    op.drop_table("media_files")
    op.drop_table("raw_messages")
    op.drop_table("entry_versions")
    op.drop_table("daily_entries")
    op.drop_table("user_settings")
    op.drop_table("users")
