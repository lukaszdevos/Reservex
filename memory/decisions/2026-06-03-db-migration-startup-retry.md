# DB Migration Startup Retry

- Date: 2026-06-03
- Decision: Normalize Postgres database URLs to the asyncpg SQLAlchemy dialect, translate `sslmode` to asyncpg's `ssl` parameter, and retry Alembic's initial database connection during container startup.
- Context: Deployment logs showed `alembic upgrade head` failing while asyncpg opened the first database connection, before migrations could run.
- Consequences: `postgres://` and `postgresql://` deployment URLs work with the async engine, managed Postgres SSL query strings remain compatible, temporary database readiness races get a bounded retry window, and real migration failures still fail the deploy.
