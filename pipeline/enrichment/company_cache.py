"""SQLite cache for company API responses. Avoids re-hitting rate-limited APIs."""
import json
import sqlite3
from datetime import datetime, timedelta, UTC
from pathlib import Path

_DB_PATH = Path("cache/company_data.db")
_TTL_DAYS = 30


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(_DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS company_cache (
            name_key        TEXT PRIMARY KEY,
            org_number      TEXT,
            foretagsapi     TEXT,
            bolagsapi       TEXT,
            fetched_at      TEXT NOT NULL
        )
    """)
    con.commit()
    return con


def _key(company_name: str, city: str) -> str:
    return f"{company_name.lower().strip()}|{city.lower().strip()}"


def get(company_name: str, city: str) -> dict | None:
    key = _key(company_name, city)
    cutoff = (datetime.now(UTC) - timedelta(days=_TTL_DAYS)).isoformat()
    with _conn() as con:
        row = con.execute(
            "SELECT foretagsapi, bolagsapi, org_number FROM company_cache WHERE name_key=? AND fetched_at>?",
            (key, cutoff),
        ).fetchone()
    if not row:
        return None
    return {
        "foretagsapi": json.loads(row[0]) if row[0] else None,
        "bolagsapi": json.loads(row[1]) if row[1] else None,
        "org_number": row[2],
    }


def put(company_name: str, city: str, org_number: str | None,
        foretagsapi: dict | None, bolagsapi: dict | None) -> None:
    key = _key(company_name, city)
    with _conn() as con:
        con.execute(
            """INSERT OR REPLACE INTO company_cache
               (name_key, org_number, foretagsapi, bolagsapi, fetched_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                key,
                org_number,
                json.dumps(foretagsapi, ensure_ascii=False) if foretagsapi else None,
                json.dumps(bolagsapi, ensure_ascii=False) if bolagsapi else None,
                datetime.now(UTC).isoformat(),
            ),
        )
