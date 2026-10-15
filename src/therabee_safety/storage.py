"""Storage abstractions with a process-local implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LockRecord:
    subject_id: str
    reason: str
    session_id: str
    triggered_at: datetime
    message_excerpt: str


class LockStorage(Protocol):
    def get(self, subject_id: str) -> LockRecord | None: ...
    def put(self, record: LockRecord) -> None: ...
    def remove(self, subject_id: str) -> bool: ...


class InMemoryLockStorage:
    """Thread-safe, nonpersistent storage intended for examples and tests."""

    def __init__(self) -> None:
        self._records: dict[str, LockRecord] = {}
        self._guard = RLock()

    def get(self, subject_id: str) -> LockRecord | None:
        with self._guard:
            return self._records.get(subject_id)

    def put(self, record: LockRecord) -> None:
        with self._guard:
            self._records[record.subject_id] = record

    def remove(self, subject_id: str) -> bool:
        with self._guard:
            return self._records.pop(subject_id, None) is not None


def new_lock(subject_id: str, session_id: str, reason: str, message: str) -> LockRecord:
    return LockRecord(
        subject_id=subject_id,
        session_id=session_id,
        reason=reason,
        triggered_at=datetime.now(timezone.utc),
        message_excerpt=message[:500],
    )
