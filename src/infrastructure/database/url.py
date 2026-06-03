"""Database URL helpers."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_ASYNC_POSTGRES_SCHEME = "postgresql+asyncpg"
_ASYNC_POSTGRES_SCHEMES = {_ASYNC_POSTGRES_SCHEME}
_SYNC_POSTGRES_SCHEMES = {"postgres", "postgresql"}
_POSTGRES_SCHEMES = _ASYNC_POSTGRES_SCHEMES | _SYNC_POSTGRES_SCHEMES


def make_async_database_url(database_url: str) -> str:
    """Return a SQLAlchemy asyncpg URL for Postgres connections."""
    parsed = urlsplit(database_url)
    if parsed.scheme not in _POSTGRES_SCHEMES:
        return database_url

    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    has_ssl = any(key == "ssl" for key, _ in query_items)
    normalized_query_items: list[tuple[str, str]] = []
    for key, value in query_items:
        if key == "sslmode":
            if not has_ssl:
                normalized_query_items.append(("ssl", value))
            continue
        normalized_query_items.append((key, value))

    return urlunsplit(
        parsed._replace(
            scheme=_ASYNC_POSTGRES_SCHEME,
            query=urlencode(normalized_query_items),
        )
    )
