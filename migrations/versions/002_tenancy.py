"""Tenancy and audit schema for Production SaaS."""

from alembic import op

revision = "002_tenancy"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          subject TEXT NOT NULL UNIQUE,
          email TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS tenant_memberships (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          role TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE UNIQUE INDEX IF NOT EXISTS tenant_memberships_tenant_user_idx
          ON tenant_memberships (tenant_id, user_id);

        CREATE TABLE IF NOT EXISTS audit_events (
          id TEXT PRIMARY KEY,
          tenant_id TEXT,
          actor_subject TEXT,
          action TEXT NOT NULL,
          resource_type TEXT,
          resource_id TEXT,
          result TEXT NOT NULL,
          metadata JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS audit_events_tenant_created_idx
          ON audit_events (tenant_id, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS audit_events;
        DROP TABLE IF EXISTS tenant_memberships;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS tenants;
        """
    )
