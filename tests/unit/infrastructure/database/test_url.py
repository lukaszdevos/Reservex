import pytest

from infrastructure.database.url import make_async_database_url


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgresql://user:pass@db.example.com:5432/reservex",
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex",
        ),
        (
            "postgres://user:pass@db.example.com:5432/reservex?sslmode=require",
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex?ssl=require",
        ),
        (
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex?sslmode=verify-full",
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex?ssl=verify-full",
        ),
        (
            "postgresql://user:pass@db.example.com:5432/reservex?ssl=true&sslmode=require",
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex?ssl=true",
        ),
        (
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex",
            "postgresql+asyncpg://user:pass@db.example.com:5432/reservex",
        ),
    ],
)
def test_make_async_database_url(database_url: str, expected: str) -> None:
    assert make_async_database_url(database_url) == expected
