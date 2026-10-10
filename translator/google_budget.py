"""Durable, atomic Google character reservations; every sent attempt counts."""
import sqlite3
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

LIMIT = 490_000
WINDOW = 32 * 86400


class BudgetExceeded(RuntimeError):
    pass


class GoogleBudget:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = Path(path), clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE IF NOT EXISTS google_attempts ("
                "id TEXT PRIMARY KEY, created_at REAL NOT NULL, period TEXT NOT NULL, "
                "characters INTEGER NOT NULL CHECK(characters>0), state TEXT NOT NULL)")
            connection.execute("CREATE INDEX IF NOT EXISTS google_attempt_time "
                               "ON google_attempts(created_at)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def snapshot(self, connection, now):
        period = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m")
        monthly, rolling = connection.execute(
            "SELECT COALESCE(SUM(CASE WHEN period=? THEN characters ELSE 0 END),0), "
            "COALESCE(SUM(CASE WHEN created_at>? THEN characters ELSE 0 END),0) "
            "FROM google_attempts WHERE state!='not_sent'", (period, now-WINDOW)).fetchone()
        next_release = connection.execute("SELECT MIN(created_at)+? FROM google_attempts "
            "WHERE state!='not_sent' AND created_at>?", (WINDOW, now-WINDOW)).fetchone()[0]
        total, attempts = connection.execute("SELECT COALESCE(SUM(characters),0), COUNT(*) "
            "FROM google_attempts WHERE state!='not_sent'").fetchone()
        return {"limit": LIMIT, "period": period, "period_timezone": "UTC",
                "monthly_characters": monthly, "safety_window_characters": rolling,
                "total_characters": total, "request_attempts": attempts,
                "remaining": max(0, LIMIT-max(monthly, rolling)),
                "blocked": max(monthly, rolling) >= LIMIT,
                "next_safety_release_at": next_release,
                "safety_window_days": 32}

    def status(self):
        with closing(self.connect()) as connection:
            return self.snapshot(connection, self.clock())

    def reserve(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Cannot submit an empty Google request")
        count, now = len(text), self.clock()
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            state = self.snapshot(connection, now)
            if count > state["remaining"]:
                raise BudgetExceeded("GOOGLE_MONTHLY_LIMIT: insufficient character budget")
            attempt = uuid.uuid4().hex
            connection.execute("INSERT INTO google_attempts VALUES (?,?,?,?,?)",
                (attempt, now, state["period"], count, "reserved"))
        return attempt

    def complete(self, attempt):
        with closing(self.connect()) as connection, connection:
            connection.execute("UPDATE google_attempts SET state='completed' "
                               "WHERE id=? AND state='reserved'", (attempt,))
