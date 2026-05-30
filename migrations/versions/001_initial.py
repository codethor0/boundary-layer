"""Initial BoundaryLayer schema."""

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_requests (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          prompt_text TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS prompt_logs (
          id TEXT PRIMARY KEY,
          prompt_request_id TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS tool_records (
          id TEXT PRIMARY KEY,
          prompt_request_id TEXT NOT NULL,
          tool_name TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS evaluation_queue (
          id TEXT PRIMARY KEY,
          prompt_request_id TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS training_queue (
          id TEXT PRIMARY KEY,
          prompt_request_id TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS deletion_audit (
          id TEXT PRIMARY KEY,
          prompt_request_id TEXT NOT NULL,
          mode TEXT NOT NULL,
          orphan_count INTEGER NOT NULL,
          complete BOOLEAN NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS write_storm_events (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          prompt_request_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS write_storm_events_tenant_created_idx
          ON write_storm_events (tenant_id, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS write_storm_events;
        DROP TABLE IF EXISTS deletion_audit;
        DROP TABLE IF EXISTS training_queue;
        DROP TABLE IF EXISTS evaluation_queue;
        DROP TABLE IF EXISTS tool_records;
        DROP TABLE IF EXISTS prompt_logs;
        DROP TABLE IF EXISTS prompt_requests;
        """
    )
