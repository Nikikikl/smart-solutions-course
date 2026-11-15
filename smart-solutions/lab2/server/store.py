"""SQLite persistence and atomic claim semantics for post-office jobs."""

from datetime import datetime, timedelta, timezone
import json
import sqlite3
import uuid


TERMINAL_STATES = {"done", "refused", "expired"}


def utc_now():
    return datetime.now(timezone.utc)


def iso_utc(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class StateConflict(RuntimeError):
    pass


class JobStore:
    def __init__(self, path, clock=utc_now):
        self.path = str(path)
        self.clock = clock
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job TEXT NOT NULL,
                    arg_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    claimed_at TEXT,
                    result_json TEXT,
                    reason TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS jobs_queue
                    ON jobs(status, created_at);
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    last_seen TEXT NOT NULL,
                    poll_interval_ms INTEGER NOT NULL,
                    status_json TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _job_from_row(row):
        if row is None:
            return None
        return {
            "id": row["id"],
            "job": row["job"],
            "arg": json.loads(row["arg_json"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "status": row["status"],
            "claimed_at": row["claimed_at"],
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "reason": row["reason"],
            "updated_at": row["updated_at"],
        }

    def create_job(self, job_type, argument, ttl_seconds):
        now = self.clock()
        job = {
            "id": uuid.uuid4().hex,
            "job": job_type,
            "arg": argument,
            "created_at": iso_utc(now),
            "expires_at": iso_utc(now + timedelta(seconds=ttl_seconds)),
            "status": "queued",
            "claimed_at": None,
            "result": None,
            "reason": None,
            "updated_at": iso_utc(now),
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs
                    (id, job, arg_json, created_at, expires_at, status,
                     claimed_at, result_json, reason, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?)
                """,
                (
                    job["id"],
                    job["job"],
                    json.dumps(job["arg"], separators=(",", ":"), sort_keys=True),
                    job["created_at"],
                    job["expires_at"],
                    job["status"],
                    job["updated_at"],
                ),
            )
        return job

    def _expire_queued(self, connection, now):
        now_text = iso_utc(now)
        connection.execute(
            """
            UPDATE jobs
               SET status = 'expired', reason = 'ttl_expired', updated_at = ?
             WHERE status = 'queued' AND expires_at <= ?
            """,
            (now_text, now_text),
        )

    def get_job(self, job_id):
        with self._connect() as connection:
            self._expire_queued(connection, self.clock())
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._job_from_row(row)

    def list_jobs(self, limit=100):
        with self._connect() as connection:
            self._expire_queued(connection, self.clock())
            rows = connection.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._job_from_row(row) for row in rows]

    def claim_next(self, lease_seconds=None):
        """Deliver the next job to the polling Atom.

        A claim is a lease: if the poll response never reached the Atom (it
        reported poll_failed), the job stays claimed without a result. An idle
        Atom never polls while it holds a job, so a claimed job older than the
        lease is handed out again, but only before its TTL. Re-delivery is safe:
        the Atom and the station both deduplicate by job id.
        """
        now = self.clock()
        now_text = iso_utc(now)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._expire_queued(connection, now)
            if lease_seconds is not None:
                lapsed = connection.execute(
                    """
                    SELECT * FROM jobs
                     WHERE status = 'claimed' AND result_json IS NULL
                       AND claimed_at <= ? AND expires_at > ?
                     ORDER BY created_at, id
                     LIMIT 1
                    """,
                    (iso_utc(now - timedelta(seconds=lease_seconds)), now_text),
                ).fetchone()
                if lapsed is not None:
                    connection.execute(
                        "UPDATE jobs SET claimed_at = ?, updated_at = ? WHERE id = ?",
                        (now_text, now_text, lapsed["id"]),
                    )
                    again = connection.execute("SELECT * FROM jobs WHERE id = ?", (lapsed["id"],)).fetchone()
                    connection.commit()
                    return self._job_from_row(again)
            row = connection.execute(
                """
                SELECT * FROM jobs
                 WHERE status = 'queued' AND expires_at > ?
                 ORDER BY created_at, id
                 LIMIT 1
                """,
                (now_text,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            changed = connection.execute(
                """
                UPDATE jobs
                   SET status = 'claimed', claimed_at = ?, updated_at = ?
                 WHERE id = ? AND status = 'queued'
                """,
                (now_text, now_text, row["id"]),
            ).rowcount
            if changed != 1:
                raise StateConflict("Job claim changed concurrently.")
            claimed = connection.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
            connection.commit()
            return self._job_from_row(claimed)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_result(self, job_id, status, result, reason):
        now_text = iso_utc(self.clock())
        result_json = (
            json.dumps(result, separators=(",", ":"), sort_keys=True)
            if result is not None
            else None
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            current = self._job_from_row(row)
            if current["status"] in {"done", "refused"}:
                same = (
                    current["status"] == status
                    and current["result"] == result
                    and current["reason"] == reason
                )
                if not same:
                    raise StateConflict("Terminal result conflicts with the stored result.")
                connection.commit()
                return current, True
            if current["status"] != "claimed":
                raise StateConflict("Only a claimed job can receive a result.")
            connection.execute(
                """
                UPDATE jobs
                   SET status = ?, result_json = ?, reason = ?, updated_at = ?
                 WHERE id = ?
                """,
                (status, result_json, reason, now_text, job_id),
            )
            saved = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            connection.commit()
            return self._job_from_row(saved), False
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def update_heartbeat(self, poll):
        seen = iso_utc(self.clock())
        status = {
            "atom_uptime_ms": poll["atom_uptime_ms"],
            "station": poll["station"],
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO devices(device_id, last_seen, poll_interval_ms, status_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    poll_interval_ms = excluded.poll_interval_ms,
                    status_json = excluded.status_json
                """,
                (
                    poll["device_id"],
                    seen,
                    poll["poll_interval_ms"],
                    json.dumps(status, separators=(",", ":"), sort_keys=True),
                ),
            )
        return self.get_device(poll["device_id"])

    def get_device(self, device_id=None):
        with self._connect() as connection:
            if device_id is None:
                row = connection.execute(
                    "SELECT * FROM devices ORDER BY last_seen DESC LIMIT 1"
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM devices WHERE device_id = ?", (device_id,)
                ).fetchone()
        if row is None:
            return None
        return {
            "device_id": row["device_id"],
            "last_seen": row["last_seen"],
            "poll_interval_ms": row["poll_interval_ms"],
            "reported": json.loads(row["status_json"]),
        }


def device_status(device, now, stale_seconds, offline_seconds):
    if device is None:
        return {"status": "offline", "last_seen": None, "device": None}
    age_seconds = max(0.0, (now - parse_utc(device["last_seen"])).total_seconds())
    if age_seconds <= stale_seconds:
        status = "online"
    elif age_seconds <= offline_seconds:
        status = "stale"
    else:
        status = "offline"
    return {
        "status": status,
        "last_seen": device["last_seen"],
        "age_seconds": age_seconds,
        "device": device,
    }
