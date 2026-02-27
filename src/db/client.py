"""Database client for persistent memory.

Supports two modes:
1. Supabase (PostgreSQL) - production, with RLS and full SQL
2. Local JSON files - for development/testing without Supabase
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "db"


class LocalStore:
    """Simple JSON file-based storage for development/testing."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, table: str) -> Path:
        return DATA_DIR / f"{table}.json"

    def _load(self, table: str) -> list[dict]:
        path = self._path(table)
        if path.exists():
            return json.loads(path.read_text())
        return []

    def _save(self, table: str, rows: list[dict]):
        path = self._path(table)
        path.write_text(json.dumps(rows, indent=2, default=str))

    def insert(self, table: str, row: dict) -> dict:
        rows = self._load(table)
        row.setdefault("created_at", datetime.now().isoformat())
        rows.append(row)
        self._save(table, rows)
        return row

    def insert_many(self, table: str, new_rows: list[dict]) -> list[dict]:
        rows = self._load(table)
        for row in new_rows:
            row.setdefault("created_at", datetime.now().isoformat())
        rows.extend(new_rows)
        self._save(table, rows)
        return new_rows

    def select(self, table: str, filters: dict | None = None) -> list[dict]:
        rows = self._load(table)
        if not filters:
            return rows
        return [r for r in rows if all(r.get(k) == v for k, v in filters.items())]

    def upsert(self, table: str, row: dict, match_key: str) -> dict:
        rows = self._load(table)
        for i, existing in enumerate(rows):
            if existing.get(match_key) == row.get(match_key):
                rows[i] = {**existing, **row, "updated_at": datetime.now().isoformat()}
                self._save(table, rows)
                return rows[i]
        return self.insert(table, row)

    def delete(self, table: str, filters: dict) -> int:
        rows = self._load(table)
        before = len(rows)
        rows = [r for r in rows if not all(r.get(k) == v for k, v in filters.items())]
        self._save(table, rows)
        return before - len(rows)


class SupabaseStore:
    """Supabase client for production persistent memory."""

    def __init__(self, url: str | None = None, key: str | None = None):
        from supabase import create_client

        self.url = url or os.environ["SUPABASE_URL"]
        self.key = key or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.client = create_client(self.url, self.key)

    def insert(self, table: str, row: dict) -> dict:
        result = self.client.table(table).insert(row).execute()
        return result.data[0] if result.data else row

    def insert_many(self, table: str, rows: list[dict]) -> list[dict]:
        result = self.client.table(table).insert(rows).execute()
        return result.data if result.data else rows

    def select(self, table: str, filters: dict | None = None) -> list[dict]:
        query = self.client.table(table).select("*")
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        result = query.execute()
        return result.data

    def upsert(self, table: str, row: dict, match_key: str) -> dict:
        result = self.client.table(table).upsert(row, on_conflict=match_key).execute()
        return result.data[0] if result.data else row

    def delete(self, table: str, filters: dict) -> int:
        query = self.client.table(table).delete()
        for k, v in filters.items():
            query = query.eq(k, v)
        result = query.execute()
        return len(result.data) if result.data else 0

    def rpc(self, function_name: str, params: dict) -> Any:
        return self.client.rpc(function_name, params).execute()


def get_store() -> LocalStore | SupabaseStore:
    """Get the appropriate store based on environment configuration."""
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        return SupabaseStore()
    return LocalStore()
