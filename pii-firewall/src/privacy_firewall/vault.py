from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class MappingVaultProtocol(Protocol):
    def put(self, tenant_id: str, case_id: str, thread_id: str, token: str, original: str, ttl_seconds: int | None = None) -> None:
        ...

    def get_case_mapping(self, tenant_id: str, case_id: str, thread_id: str) -> dict[str, str]:
        ...

    def forget_case(self, tenant_id: str, case_id: str, thread_id: str) -> int:
        ...

    def purge_expired(self) -> int:
        ...


@dataclass
class InMemoryMappingVault:
    # key: (tenant, case, thread) -> token -> original
    _store: dict[tuple[str, str, str], dict[str, str]] = field(default_factory=dict)
    # key: (tenant, case, thread) -> token -> unix expiry timestamp (None = no expiry)
    _expiry: dict[tuple[str, str, str], dict[str, int]] = field(default_factory=dict)

    def put(self, tenant_id: str, case_id: str, thread_id: str, token: str, original: str, ttl_seconds: int | None = None) -> None:
        key = (tenant_id, case_id, thread_id)
        if key not in self._store:
            self._store[key] = {}
            self._expiry[key] = {}
        self._store[key][token] = original
        if ttl_seconds and ttl_seconds > 0:
            self._expiry[key][token] = int(time.time()) + ttl_seconds
        else:
            self._expiry[key].pop(token, None)

    def get_case_mapping(self, tenant_id: str, case_id: str, thread_id: str) -> dict[str, str]:
        self.purge_expired()
        return dict(self._store.get((tenant_id, case_id, thread_id), {}))

    def forget_case(self, tenant_id: str, case_id: str, thread_id: str) -> int:
        key = (tenant_id, case_id, thread_id)
        mapping = self._store.pop(key, {})
        self._expiry.pop(key, None)
        return len(mapping)

    def purge_expired(self) -> int:
        now = int(time.time())
        count = 0
        for key in list(self._store.keys()):
            expiry_map = self._expiry.get(key, {})
            store_map = self._store[key]
            expired = [t for t, exp in expiry_map.items() if exp <= now]
            for token in expired:
                store_map.pop(token, None)
                expiry_map.pop(token, None)
                count += 1
        return count


@dataclass
class SQLiteMappingVault:
    """Persistent mapping vault with TTL support.

    Notes:
    - This class intentionally uses stdlib sqlite3 for zero external dependencies.
    - For production, prefer a managed database plus encryption-at-rest and KMS.
    """

    db_path: str

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mapping_vault (
                    tenant_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    original TEXT NOT NULL,
                    expires_at INTEGER,
                    PRIMARY KEY (tenant_id, case_id, thread_id, token)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mapping_expiry ON mapping_vault (expires_at)"
            )

    def put(self, tenant_id: str, case_id: str, thread_id: str, token: str, original: str, ttl_seconds: int | None = None) -> None:
        expires_at = int(time.time()) + ttl_seconds if ttl_seconds and ttl_seconds > 0 else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO mapping_vault (tenant_id, case_id, thread_id, token, original, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, case_id, thread_id, token)
                DO UPDATE SET original = excluded.original, expires_at = excluded.expires_at
                """,
                (tenant_id, case_id, thread_id, token, original, expires_at),
            )

    def get_case_mapping(self, tenant_id: str, case_id: str, thread_id: str) -> dict[str, str]:
        self.purge_expired()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT token, original
                FROM mapping_vault
                WHERE tenant_id = ? AND case_id = ? AND thread_id = ?
                """,
                (tenant_id, case_id, thread_id),
            ).fetchall()
        return {token: original for token, original in rows}

    def forget_case(self, tenant_id: str, case_id: str, thread_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                DELETE FROM mapping_vault
                WHERE tenant_id = ? AND case_id = ? AND thread_id = ?
                """,
                (tenant_id, case_id, thread_id),
            )
            return cur.rowcount

    def purge_expired(self) -> int:
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM mapping_vault WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (now,),
            )
            return cur.rowcount
