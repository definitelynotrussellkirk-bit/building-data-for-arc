#!/usr/bin/env python3
"""Coordinate KIMI generator reviews through SQLite.

SQLite is the mutable coordination surface.  The existing assignment and
review JSONL files remain compatibility artifacts for the queue builder and
independent monitor.  Reviews are staged in the database first and are only
appended to the legacy ledger after the existing pre-append validator passes.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import math
import secrets
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "tmp" / "kimi_swarm" / "review_coordination.sqlite3"
DEFAULT_REVIEWS = ROOT / "data" / "derived" / "kimi_generator_reviews.jsonl"
DEFAULT_ASSIGNMENTS = (
    ROOT / "data" / "derived" / "kimi_generator_assignment.jsonl"
)
DEFAULT_VETOES = (
    ROOT / "tmp" / "kimi_swarm" / "orchestrator_semantic_vetoes.json"
)
DEFAULT_MONITOR_STATE = (
    ROOT / "tmp" / "kimi_swarm" / "review_monitor_state.json"
)
VALID_FEEDBACK_STATES = ("open", "acknowledged", "resolved")
VALID_SEVERITIES = ("info", "suggestion", "warning", "blocking")
SCHEMA_VERSION = 1


class CoordinationError(RuntimeError):
    """Raised for a safe, user-correctable coordination failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def payload_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def review_subject_hash(record: dict[str, Any]) -> str | None:
    after = record.get("after")
    after = after if isinstance(after, dict) else {}
    metrics = after.get("metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    candidates = (
        record.get("generator_snapshot_sha256"),
        record.get("generator_sha256"),
        after.get("generator_snapshot_sha256"),
        after.get("generator_sha256"),
        metrics.get("generator_sha256"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    conn.execute("pragma busy_timeout = 30000")
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma synchronous = full")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists schema_meta (
            key text primary key,
            value text not null
        );

        create table if not exists review_records (
            id integer primary key autoincrement,
            task_id text not null,
            recorded_at text not null,
            status text,
            reviewer text,
            subject_hash text,
            digest text not null unique,
            source_ref text,
            payload_json text not null
        );
        create index if not exists review_records_task_id_id
            on review_records(task_id, id desc);

        create table if not exists published_reviews (
            review_id integer not null,
            ledger_path text not null,
            digest text not null,
            published_at text not null,
            primary key(review_id, ledger_path),
            foreign key(review_id) references review_records(id)
        );

        create table if not exists semantic_veto_snapshots (
            id integer primary key autoincrement,
            task_id text not null,
            recorded_at text not null,
            active integer not null check(active in (0, 1)),
            digest text not null unique,
            payload_json text not null
        );
        create index if not exists semantic_veto_task_id_id
            on semantic_veto_snapshots(task_id, id desc);

        create table if not exists semantic_veto_current (
            task_id text primary key,
            active integer not null check(active in (0, 1)),
            synced_at text not null,
            digest text not null,
            payload_json text not null
        );

        create table if not exists assignment_rows (
            task_id text primary key,
            queue_position integer not null,
            queue_rank integer,
            status text,
            priority_score real,
            active_semantic_veto integer not null default 0,
            synced_at text not null,
            payload_json text not null
        );
        create index if not exists assignment_rows_queue
            on assignment_rows(status, queue_position);

        create table if not exists monitor_audits (
            task_id text primary key,
            gate_status text,
            source_hash text,
            checked_at text,
            synced_at text not null,
            payload_json text not null
        );

        create table if not exists feedback (
            id integer primary key autoincrement,
            task_id text,
            audience text not null,
            category text not null,
            severity text not null,
            status text not null,
            message text not null,
            created_at text not null,
            created_by text not null,
            acknowledged_at text,
            acknowledged_by text,
            resolved_at text,
            resolved_by text,
            metadata_json text not null
        );
        create index if not exists feedback_inbox
            on feedback(audience, status, task_id, id);

        create table if not exists feedback_events (
            id integer primary key autoincrement,
            feedback_id integer not null,
            event text not null,
            actor text not null,
            created_at text not null,
            detail text,
            foreign key(feedback_id) references feedback(id)
        );

        create table if not exists task_claims (
            task_id text primary key,
            worker text not null,
            claimed_at text not null,
            renewed_at text not null,
            expires_at text not null,
            note text,
            foreign key(task_id) references assignment_rows(task_id)
        );

        create table if not exists claim_events (
            id integer primary key autoincrement,
            task_id text not null,
            worker text not null,
            event text not null,
            created_at text not null,
            detail text
        );
        """
    )
    conn.execute(
        """
        insert into schema_meta(key, value) values ('schema_version', ?)
        on conflict(key) do update set value = excluded.value
        """,
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CoordinationError(f"cannot read {path}: {exc}") from exc


def _read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CoordinationError(
                        f"{path}:{line_number}: invalid JSON: {exc}"
                    ) from exc
                if not isinstance(row, dict):
                    raise CoordinationError(
                        f"{path}:{line_number}: expected a JSON object"
                    )
                rows.append((line_number, row))
    except OSError as exc:
        raise CoordinationError(f"cannot read {path}: {exc}") from exc
    return rows


def _task_id(record: dict[str, Any], *, source: str) -> str:
    task_id = record.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise CoordinationError(f"{source}: missing non-empty task_id")
    return task_id.strip()


def store_review(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    *,
    source_ref: str | None = None,
) -> tuple[int, bool]:
    task_id = _task_id(record, source=source_ref or "review record")
    digest = payload_digest(record)
    before = conn.total_changes
    conn.execute(
        """
        insert into review_records(
            task_id, recorded_at, status, reviewer, subject_hash,
            digest, source_ref, payload_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(digest) do nothing
        """,
        (
            task_id,
            utc_now(),
            str(record.get("status") or "") or None,
            str(record.get("reviewer") or record.get("reviewed_by") or "")
            or None,
            review_subject_hash(record),
            digest,
            source_ref,
            canonical_json(record),
        ),
    )
    inserted = conn.total_changes > before
    row = conn.execute(
        "select id from review_records where digest = ?", (digest,)
    ).fetchone()
    assert row is not None
    return int(row["id"]), inserted


def _iter_veto_entries(value: Any) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        for task_id, payload in value.items():
            if isinstance(payload, dict):
                normalized = dict(payload)
                normalized.setdefault("task_id", task_id)
                yield str(task_id), normalized
    elif isinstance(value, list):
        for payload in value:
            if isinstance(payload, dict):
                yield _task_id(payload, source="semantic veto"), payload


def semantic_veto_is_active(payload: Any) -> bool:
    """Mirror the queue/monitor fail-closed self-clearance rule."""
    if not isinstance(payload, dict):
        return False
    if payload.get("active") is True:
        return True
    if not payload.get("orchestrator_clearance"):
        return False
    return not (
        payload.get("clearance_authority")
        == "independent_codex_monitor"
        and bool(payload.get("independent_clearance_at"))
    )


def sync_sources(
    conn: sqlite3.Connection,
    *,
    reviews_path: Path,
    assignments_path: Path,
    vetoes_path: Path,
    monitor_state_path: Path,
) -> dict[str, int]:
    reviews = _read_jsonl(reviews_path)
    assignments = _read_jsonl(assignments_path)
    vetoes = _read_json(vetoes_path, {})
    monitor_state = _read_json(monitor_state_path, {})
    counts = {
        "reviews_seen": len(reviews),
        "reviews_added": 0,
        "assignments": len(assignments),
        "vetoes_seen": 0,
        "vetoes_added": 0,
        "monitor_audits": 0,
    }
    synced_at = utc_now()
    with conn:
        for line_number, review in reviews:
            _, inserted = store_review(
                conn,
                review,
                source_ref=f"{reviews_path}:{line_number}",
            )
            counts["reviews_added"] += int(inserted)

        conn.execute(
            """
            create temporary table if not exists assignment_sync_seen (
                task_id text primary key
            )
            """
        )
        conn.execute("delete from assignment_sync_seen")
        for position, (_, assignment) in enumerate(assignments, 1):
            task_id = _task_id(
                assignment, source=f"{assignments_path}:{position}"
            )
            conn.execute(
                "insert into assignment_sync_seen(task_id) values (?)",
                (task_id,),
            )
            conn.execute(
                """
                insert into assignment_rows(
                    task_id, queue_position, queue_rank, status,
                    priority_score, active_semantic_veto, synced_at,
                    payload_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(task_id) do update set
                    queue_position = excluded.queue_position,
                    queue_rank = excluded.queue_rank,
                    status = excluded.status,
                    priority_score = excluded.priority_score,
                    active_semantic_veto =
                        excluded.active_semantic_veto,
                    synced_at = excluded.synced_at,
                    payload_json = excluded.payload_json
                """,
                (
                    task_id,
                    position,
                    _optional_int(assignment.get("queue_rank")),
                    str(assignment.get("status") or "") or None,
                    _optional_float(assignment.get("priority_score")),
                    int(bool(assignment.get("active_semantic_veto"))),
                    synced_at,
                    canonical_json(assignment),
                ),
            )
        stale_claims = conn.execute(
            """
            select c.task_id, c.worker
            from task_claims c
            left join assignment_rows a on a.task_id = c.task_id
            where not exists (
                    select 1 from assignment_sync_seen s
                    where s.task_id = c.task_id
                )
               or a.status != 'pending'
            """
        ).fetchall()
        for claim in stale_claims:
            conn.execute(
                """
                insert into claim_events(
                    task_id, worker, event, created_at, detail
                ) values (?, ?, 'released', ?,
                          'task left the pending assignment queue')
                """,
                (claim["task_id"], claim["worker"], synced_at),
            )
        conn.execute(
            """
            delete from task_claims
            where not exists (
                    select 1 from assignment_sync_seen s
                    where s.task_id = task_claims.task_id
                )
               or exists (
                    select 1 from assignment_rows a
                    where a.task_id = task_claims.task_id
                      and a.status != 'pending'
                )
            """
        )
        conn.execute(
            """
            delete from assignment_rows
            where not exists (
                select 1 from assignment_sync_seen s
                where s.task_id = assignment_rows.task_id
            )
            """
        )

        conn.execute("delete from semantic_veto_current")
        for task_id, veto in _iter_veto_entries(vetoes):
            counts["vetoes_seen"] += 1
            digest = payload_digest({"task_id": task_id, "payload": veto})
            before = conn.total_changes
            conn.execute(
                """
                insert into semantic_veto_snapshots(
                    task_id, recorded_at, active, digest, payload_json
                ) values (?, ?, ?, ?, ?)
                on conflict(digest) do nothing
                """,
                (
                    task_id,
                    synced_at,
                    int(semantic_veto_is_active(veto)),
                    digest,
                    canonical_json(veto),
                ),
            )
            counts["vetoes_added"] += int(conn.total_changes > before)
            conn.execute(
                """
                insert into semantic_veto_current(
                    task_id, active, synced_at, digest, payload_json
                ) values (?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    int(semantic_veto_is_active(veto)),
                    synced_at,
                    digest,
                    canonical_json(veto),
                ),
            )

        conn.execute("delete from monitor_audits")
        audited = (
            monitor_state.get("audited", {})
            if isinstance(monitor_state, dict)
            else {}
        )
        if isinstance(audited, dict):
            for task_id, audit in audited.items():
                if not isinstance(audit, dict):
                    continue
                conn.execute(
                    """
                    insert into monitor_audits(
                        task_id, gate_status, source_hash, checked_at,
                        synced_at, payload_json
                    ) values (?, ?, ?, ?, ?, ?)
                    on conflict(task_id) do update set
                        gate_status = excluded.gate_status,
                        source_hash = excluded.source_hash,
                        checked_at = excluded.checked_at,
                        synced_at = excluded.synced_at,
                        payload_json = excluded.payload_json
                    """,
                    (
                        str(task_id),
                        str(
                            audit.get("gate_status")
                            or audit.get("status")
                            or (
                                "PASS"
                                if audit.get("passed") is True
                                else "FAIL"
                                if audit.get("passed") is False
                                else ""
                            )
                            or ""
                        )
                        or None,
                        str(
                            audit.get("generator_snapshot_sha256")
                            or audit.get("source_hash")
                            or audit.get("subject_hash")
                            or ""
                        )
                        or None,
                        str(
                            audit.get("checked_at")
                            or audit.get("audited_at")
                            or ""
                        )
                        or None,
                        synced_at,
                        canonical_json(audit),
                    ),
                )
                counts["monitor_audits"] += 1
        _purge_expired_claims(conn, actor="sync")
    return counts


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_review(
    conn: sqlite3.Connection, task_id: str
) -> sqlite3.Row | None:
    return conn.execute(
        """
        select * from review_records
        where task_id = ?
        order by id desc
        limit 1
        """,
        (task_id,),
    ).fetchone()


def validate_review_with_existing_gate(
    record: dict[str, Any],
) -> list[str]:
    validator = ROOT / "scripts" / "build_kimi_generator_assignment.py"
    stage_dir = ROOT / "tmp" / "kimi_swarm" / "validation"
    stage_dir.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="db-review-",
            suffix=".json",
            dir=stage_dir,
            delete=False,
        ) as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        result = subprocess.run(
            [
                sys.executable,
                str(validator),
                "--validate-record",
                str(temp_path),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode == 0:
            return []
        output = result.stdout.strip()
        return [output or f"validator exited {result.returncode}"]
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def publish_review(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    ledger_path: Path,
    validator: Callable[[dict[str, Any]], list[str]]
    | None = validate_review_with_existing_gate,
) -> dict[str, Any]:
    row = latest_review(conn, task_id)
    if row is None:
        raise CoordinationError(f"no staged review exists for {task_id}")
    record = json.loads(row["payload_json"])
    if validator is not None:
        errors = validator(record)
        if errors:
            raise CoordinationError(
                "pre-append validation failed:\n" + "\n".join(errors)
            )

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    digest = str(row["digest"])
    already_present = False
    try:
        with ledger_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CoordinationError(
                        f"{ledger_path}:{line_number}: invalid JSON; "
                        "refusing to append"
                    ) from exc
                if payload_digest(existing) == digest:
                    already_present = True
                    break
            if not already_present:
                handle.seek(0, os.SEEK_END)
                handle.write(canonical_json(record) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        raise CoordinationError(
            f"cannot publish review to {ledger_path}: {exc}"
        ) from exc

    with conn:
        conn.execute(
            """
            insert into published_reviews(
                review_id, ledger_path, digest, published_at
            ) values (?, ?, ?, ?)
            on conflict(review_id, ledger_path) do update set
                digest = excluded.digest,
                published_at = excluded.published_at
            """,
            (
                int(row["id"]),
                str(ledger_path.resolve()),
                digest,
                utc_now(),
            ),
        )
    return {
        "task_id": task_id,
        "review_id": int(row["id"]),
        "digest": digest,
        "ledger": str(ledger_path),
        "appended": not already_present,
        "already_present": already_present,
    }


def add_feedback(
    conn: sqlite3.Connection,
    *,
    task_id: str | None,
    audience: str,
    category: str,
    severity: str,
    message: str,
    created_by: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    if severity not in VALID_SEVERITIES:
        raise CoordinationError(
            f"severity must be one of {', '.join(VALID_SEVERITIES)}"
        )
    if not message.strip():
        raise CoordinationError("feedback message cannot be empty")
    now = utc_now()
    with conn:
        cursor = conn.execute(
            """
            insert into feedback(
                task_id, audience, category, severity, status, message,
                created_at, created_by, metadata_json
            ) values (?, ?, ?, ?, 'open', ?, ?, ?, ?)
            """,
            (
                task_id or None,
                audience,
                category,
                severity,
                message.strip(),
                now,
                created_by,
                canonical_json(metadata or {}),
            ),
        )
        feedback_id = int(cursor.lastrowid)
        conn.execute(
            """
            insert into feedback_events(
                feedback_id, event, actor, created_at, detail
            ) values (?, 'created', ?, ?, ?)
            """,
            (feedback_id, created_by, now, category),
        )
    return feedback_id


def transition_feedback(
    conn: sqlite3.Connection,
    feedback_id: int,
    *,
    status: str,
    actor: str,
    detail: str | None = None,
) -> None:
    if status not in ("acknowledged", "resolved"):
        raise CoordinationError("feedback can only be acknowledged or resolved")
    current = conn.execute(
        "select status from feedback where id = ?", (feedback_id,)
    ).fetchone()
    if current is None:
        raise CoordinationError(f"feedback {feedback_id} does not exist")
    if current["status"] == "resolved" and status == "acknowledged":
        raise CoordinationError("resolved feedback cannot be moved backward")
    now = utc_now()
    if status == "acknowledged":
        update = """
            update feedback set
                status = 'acknowledged',
                acknowledged_at = coalesce(acknowledged_at, ?),
                acknowledged_by = coalesce(acknowledged_by, ?)
            where id = ?
        """
        params: tuple[Any, ...] = (now, actor, feedback_id)
    else:
        update = """
            update feedback set
                status = 'resolved',
                acknowledged_at = coalesce(acknowledged_at, ?),
                acknowledged_by = coalesce(acknowledged_by, ?),
                resolved_at = ?,
                resolved_by = ?
            where id = ?
        """
        params = (now, actor, now, actor, feedback_id)
    with conn:
        conn.execute(update, params)
        conn.execute(
            """
            insert into feedback_events(
                feedback_id, event, actor, created_at, detail
            ) values (?, ?, ?, ?, ?)
            """,
            (feedback_id, status, actor, now, detail),
        )


def feedback_inbox(
    conn: sqlite3.Connection,
    *,
    task_id: str | None,
    audience: str | None,
    status: str | None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if task_id:
        clauses.append("(task_id = ? or task_id is null)")
        values.append(task_id)
    if audience:
        clauses.append("audience = ?")
        values.append(audience)
    if status:
        clauses.append("status = ?")
        values.append(status)
    where = " where " + " and ".join(clauses) if clauses else ""
    rows = conn.execute(
        "select * from feedback"
        + where
        + """
          order by
            case severity
              when 'blocking' then 0
              when 'warning' then 1
              when 'suggestion' then 2
              else 3
            end,
            id
        """,
        values,
    ).fetchall()
    return [_feedback_row(row) for row in rows]


def _feedback_row(row: sqlite3.Row) -> dict[str, Any]:
    out = dict(row)
    out["metadata"] = json.loads(out.pop("metadata_json"))
    return out


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _purge_expired_claims(
    conn: sqlite3.Connection, *, actor: str
) -> int:
    now = datetime.now(timezone.utc)
    rows = conn.execute("select * from task_claims").fetchall()
    expired = [row for row in rows if _parse_utc(row["expires_at"]) <= now]
    for row in expired:
        conn.execute(
            """
            insert into claim_events(
                task_id, worker, event, created_at, detail
            ) values (?, ?, 'expired', ?, ?)
            """,
            (
                row["task_id"],
                row["worker"],
                utc_now(),
                f"noticed by {actor}",
            ),
        )
        conn.execute(
            "delete from task_claims where task_id = ?", (row["task_id"],)
        )
    return len(expired)


def claim_task(
    conn: sqlite3.Connection,
    *,
    worker: str,
    task_id: str | None,
    lease_minutes: int,
    note: str | None,
    require_existing: bool = False,
    random_assignment: bool = False,
    random_seed: int | None = None,
    priority_weighted_random: bool = False,
) -> dict[str, Any]:
    if lease_minutes < 1:
        raise CoordinationError("lease minutes must be positive")
    if random_assignment and task_id is not None:
        raise CoordinationError(
            "random assignment cannot be combined with a named task"
        )
    if random_assignment and require_existing:
        raise CoordinationError("an existing claim cannot be renewed randomly")
    if random_seed is not None and not random_assignment:
        raise CoordinationError("a random seed requires random assignment")
    if priority_weighted_random and not random_assignment:
        raise CoordinationError(
            "priority-weighted selection requires random assignment"
        )
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat(timespec="seconds")
    expires = (now_dt + timedelta(minutes=lease_minutes)).isoformat(
        timespec="seconds"
    )
    conn.execute("begin immediate")
    try:
        _purge_expired_claims(conn, actor=worker)
        candidate_count: int | None = None
        selected_seed: int | None = None
        if task_id is None:
            if random_assignment:
                candidates = conn.execute(
                    """
                    select a.task_id, a.priority_score
                    from assignment_rows a
                    left join task_claims c on c.task_id = a.task_id
                    where a.status = 'pending' and c.task_id is null
                    order by a.task_id
                    """
                ).fetchall()
                candidate_count = len(candidates)
                selected_seed = (
                    random_seed
                    if random_seed is not None
                    else secrets.randbits(64)
                )
                if candidates and priority_weighted_random:
                    weights = [
                        1.0 + math.sqrt(
                            max(0.0, float(row["priority_score"] or 0.0))
                        )
                        for row in candidates
                    ]
                    selected = random.Random(selected_seed).choices(
                        candidates,
                        weights=weights,
                        k=1,
                    )[0]
                else:
                    selected = (
                        random.Random(selected_seed).choice(candidates)
                        if candidates
                        else None
                    )
            else:
                selected = conn.execute(
                    """
                    select a.task_id
                    from assignment_rows a
                    left join task_claims c on c.task_id = a.task_id
                    where a.status = 'pending' and c.task_id is null
                    order by
                        a.active_semantic_veto desc,
                        coalesce(a.queue_rank, a.queue_position),
                        a.queue_position
                    limit 1
                    """
                ).fetchone()
            if selected is None:
                raise CoordinationError("no unclaimed pending task is available")
            task_id = str(selected["task_id"])
        assignment = conn.execute(
            "select status from assignment_rows where task_id = ?", (task_id,)
        ).fetchone()
        if assignment is None:
            raise CoordinationError(
                f"{task_id} is not in the synchronized assignment queue"
            )
        current = conn.execute(
            "select * from task_claims where task_id = ?", (task_id,)
        ).fetchone()
        if require_existing and current is None:
            raise CoordinationError(
                f"{task_id} has no active claim to renew"
            )
        if current is not None and current["worker"] != worker:
            raise CoordinationError(
                f"{task_id} is claimed by {current['worker']} until "
                f"{current['expires_at']}"
            )
        if current is None and assignment["status"] != "pending":
            raise CoordinationError(
                f"{task_id} is {assignment['status']!r}, not pending"
            )
        event = "renewed" if current is not None else "claimed"
        conn.execute(
            """
            insert into task_claims(
                task_id, worker, claimed_at, renewed_at, expires_at, note
            ) values (?, ?, ?, ?, ?, ?)
            on conflict(task_id) do update set
                worker = excluded.worker,
                renewed_at = excluded.renewed_at,
                expires_at = excluded.expires_at,
                note = coalesce(excluded.note, task_claims.note)
            """,
            (task_id, worker, now, now, expires, note),
        )
        conn.execute(
            """
            insert into claim_events(
                task_id, worker, event, created_at, detail
            ) values (?, ?, ?, ?, ?)
            """,
            (task_id, worker, event, now, note),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {
        "task_id": task_id,
        "worker": worker,
        "event": event,
        "expires_at": expires,
        "assignment_mode": "random" if random_assignment else "queue",
        **(
            {
                "selection_seed": selected_seed,
                "candidate_count": candidate_count,
                "selection_strategy": (
                    "priority_weighted_random"
                    if priority_weighted_random
                    else "uniform_random"
                ),
            }
            if random_assignment
            else {}
        ),
    }


def release_claim(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    worker: str,
    outcome: str,
) -> None:
    conn.execute("begin immediate")
    try:
        current = conn.execute(
            "select * from task_claims where task_id = ?", (task_id,)
        ).fetchone()
        if current is None:
            raise CoordinationError(f"{task_id} has no active claim")
        if current["worker"] != worker:
            raise CoordinationError(
                f"{task_id} is claimed by {current['worker']}, not {worker}"
            )
        conn.execute(
            """
            insert into claim_events(
                task_id, worker, event, created_at, detail
            ) values (?, ?, 'released', ?, ?)
            """,
            (task_id, worker, utc_now(), outcome),
        )
        conn.execute(
            "delete from task_claims where task_id = ?", (task_id,)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def task_snapshot(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    review = latest_review(conn, task_id)
    assignment = conn.execute(
        "select * from assignment_rows where task_id = ?", (task_id,)
    ).fetchone()
    veto = conn.execute(
        """
        select * from semantic_veto_current
        where task_id = ?
        """,
        (task_id,),
    ).fetchone()
    monitor = conn.execute(
        "select * from monitor_audits where task_id = ?", (task_id,)
    ).fetchone()
    claim = conn.execute(
        "select * from task_claims where task_id = ?", (task_id,)
    ).fetchone()
    return {
        "task_id": task_id,
        "assignment": json.loads(assignment["payload_json"])
        if assignment
        else None,
        "claim": dict(claim) if claim else None,
        "latest_review": json.loads(review["payload_json"])
        if review
        else None,
        "latest_review_db": {
            key: review[key]
            for key in (
                "id",
                "recorded_at",
                "digest",
                "subject_hash",
                "source_ref",
            )
        }
        if review
        else None,
        "semantic_veto": json.loads(veto["payload_json"])
        if veto
        else None,
        "monitor_audit": json.loads(monitor["payload_json"])
        if monitor
        else None,
        "feedback": feedback_inbox(
            conn,
            task_id=task_id,
            audience=None,
            status=None,
        ),
    }


def database_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    feedback_counts = {
        row["status"]: int(row["count"])
        for row in conn.execute(
            "select status, count(*) as count from feedback group by status"
        )
    }
    active_vetoes = conn.execute(
        """
        select count(*) as count
        from semantic_veto_current
        where active = 1
        """
    ).fetchone()
    return {
        "schema_version": SCHEMA_VERSION,
        "review_records": _count(conn, "review_records"),
        "reviewed_tasks": int(
            conn.execute(
                "select count(distinct task_id) as count from review_records"
            ).fetchone()["count"]
        ),
        "published_reviews": _count(conn, "published_reviews"),
        "assignments": _count(conn, "assignment_rows"),
        "pending_assignments": int(
            conn.execute(
                """
                select count(*) as count from assignment_rows
                where status = 'pending'
                """
            ).fetchone()["count"]
        ),
        "active_semantic_vetoes": int(active_vetoes["count"]),
        "monitor_audits": _count(conn, "monitor_audits"),
        "feedback": {
            state: feedback_counts.get(state, 0)
            for state in VALID_FEEDBACK_STATES
        },
        "active_claims": _count(conn, "task_claims"),
    }


def _count(conn: sqlite3.Connection, table: str) -> int:
    allowed = {
        "review_records",
        "published_reviews",
        "assignment_rows",
        "monitor_audits",
        "task_claims",
    }
    if table not in allowed:
        raise ValueError(table)
    return int(
        conn.execute(f"select count(*) as count from {table}").fetchone()[
            "count"
        ]
    )


def _load_record(path: Path) -> dict[str, Any]:
    try:
        value = (
            json.load(sys.stdin)
            if str(path) == "-"
            else json.loads(path.read_text())
        )
    except (OSError, json.JSONDecodeError) as exc:
        source = "stdin" if str(path) == "-" else str(path)
        raise CoordinationError(
            f"cannot read staged review from {source}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise CoordinationError(f"{path}: expected one JSON object")
    _task_id(value, source=str(path))
    return value


def _message_from_args(args: argparse.Namespace) -> str:
    if args.message is not None:
        return args.message
    if args.message_file is not None:
        try:
            return args.message_file.read_text()
        except OSError as exc:
            raise CoordinationError(
                f"cannot read {args.message_file}: {exc}"
            ) from exc
    raise CoordinationError("provide --message or --message-file")


def _print_feedback(rows: list[dict[str, Any]], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if not rows:
        print("No matching feedback.")
        return
    for row in rows:
        scope = row["task_id"] or "*"
        print(
            f"#{row['id']} [{row['severity']}/{row['status']}] "
            f"{scope} {row['category']}: {row['message']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument(
        "--assignments", type=Path, default=DEFAULT_ASSIGNMENTS
    )
    parser.add_argument("--vetoes", type=Path, default=DEFAULT_VETOES)
    parser.add_argument(
        "--monitor-state", type=Path, default=DEFAULT_MONITOR_STATE
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="create or migrate the database")
    subparsers.add_parser(
        "sync", help="import current JSONL and monitor compatibility artifacts"
    )

    put_review_parser = subparsers.add_parser(
        "put-review", help="stage one review JSON object in SQLite"
    )
    put_review_parser.add_argument(
        "record",
        type=Path,
        help="path to one JSON object, or - to read it from stdin",
    )
    put_review_parser.add_argument(
        "--publish",
        action="store_true",
        help="run the existing validator and idempotently append to JSONL",
    )

    publish_parser = subparsers.add_parser(
        "publish-review",
        help="validate and publish the latest staged review for a task",
    )
    publish_parser.add_argument("task_id")

    add_parser = subparsers.add_parser(
        "add-feedback", help="add durable feedback to a worker inbox"
    )
    add_parser.add_argument("--task-id")
    add_parser.add_argument("--audience", default="kimi")
    add_parser.add_argument("--category", default="review_method")
    add_parser.add_argument(
        "--severity", choices=VALID_SEVERITIES, default="suggestion"
    )
    add_parser.add_argument("--created-by", default="codex")
    message_group = add_parser.add_mutually_exclusive_group(required=True)
    message_group.add_argument("--message")
    message_group.add_argument("--message-file", type=Path)

    inbox_parser = subparsers.add_parser(
        "inbox", help="list feedback, including global feedback for a task"
    )
    inbox_parser.add_argument("--task-id")
    inbox_parser.add_argument("--audience", default="kimi")
    inbox_parser.add_argument(
        "--status", choices=VALID_FEEDBACK_STATES, default="open"
    )
    inbox_parser.add_argument("--all-audiences", action="store_true")
    inbox_parser.add_argument("--all-statuses", action="store_true")
    inbox_parser.add_argument("--json", action="store_true")

    for command, help_text in (
        ("ack-feedback", "acknowledge a feedback item"),
        ("resolve-feedback", "resolve a feedback item"),
    ):
        transition_parser = subparsers.add_parser(command, help=help_text)
        transition_parser.add_argument("feedback_id", type=int)
        transition_parser.add_argument("--actor", default="kimi")
        transition_parser.add_argument("--detail")

    claim_parser = subparsers.add_parser(
        "claim", help="atomically claim a pending task or a named task"
    )
    claim_parser.add_argument("task_id", nargs="?")
    claim_parser.add_argument("--worker", required=True)
    claim_parser.add_argument("--minutes", type=int, default=180)
    claim_parser.add_argument("--note")
    claim_parser.add_argument(
        "--random",
        action="store_true",
        help=(
            "choose uniformly from currently unclaimed pending tasks; "
            "the claim remains atomic"
        ),
    )
    claim_parser.add_argument(
        "--seed",
        type=int,
        help="replayable random-selection seed; requires --random",
    )
    claim_parser.add_argument(
        "--priority-weighted-random",
        action="store_true",
        help=(
            "with --random, bias selection toward higher priority_score "
            "while preserving a nonzero chance for every pending task"
        ),
    )

    renew_parser = subparsers.add_parser(
        "renew", help="renew a worker's existing task claim"
    )
    renew_parser.add_argument("task_id")
    renew_parser.add_argument("--worker", required=True)
    renew_parser.add_argument("--minutes", type=int, default=180)
    renew_parser.add_argument("--note")

    release_parser = subparsers.add_parser(
        "release", help="release a worker's task claim"
    )
    release_parser.add_argument("task_id")
    release_parser.add_argument("--worker", required=True)
    release_parser.add_argument("--outcome", default="handoff")

    show_parser = subparsers.add_parser(
        "show", help="show the current coordinated state for one task"
    )
    show_parser.add_argument("task_id")

    subparsers.add_parser("stats", help="print database coordination counts")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        with connect_db(args.db) as conn:
            if args.command == "init":
                print(
                    json.dumps(
                        {
                            "database": str(args.db),
                            "schema_version": SCHEMA_VERSION,
                        },
                        indent=2,
                    )
                )
            elif args.command == "sync":
                print(
                    json.dumps(
                        sync_sources(
                            conn,
                            reviews_path=args.reviews,
                            assignments_path=args.assignments,
                            vetoes_path=args.vetoes,
                            monitor_state_path=args.monitor_state,
                        ),
                        indent=2,
                    )
                )
            elif args.command == "put-review":
                record = _load_record(args.record)
                with conn:
                    review_id, inserted = store_review(
                        conn, record, source_ref=str(args.record)
                    )
                result: dict[str, Any] = {
                    "task_id": record["task_id"],
                    "review_id": review_id,
                    "inserted": inserted,
                    "digest": payload_digest(record),
                }
                if args.publish:
                    result["publication"] = publish_review(
                        conn,
                        str(record["task_id"]),
                        ledger_path=args.reviews,
                    )
                print(json.dumps(result, indent=2))
            elif args.command == "publish-review":
                print(
                    json.dumps(
                        publish_review(
                            conn,
                            args.task_id,
                            ledger_path=args.reviews,
                        ),
                        indent=2,
                    )
                )
            elif args.command == "add-feedback":
                feedback_id = add_feedback(
                    conn,
                    task_id=args.task_id,
                    audience=args.audience,
                    category=args.category,
                    severity=args.severity,
                    message=_message_from_args(args),
                    created_by=args.created_by,
                )
                print(json.dumps({"feedback_id": feedback_id}, indent=2))
            elif args.command == "inbox":
                rows = feedback_inbox(
                    conn,
                    task_id=args.task_id,
                    audience=None if args.all_audiences else args.audience,
                    status=None if args.all_statuses else args.status,
                )
                _print_feedback(rows, as_json=args.json)
            elif args.command in ("ack-feedback", "resolve-feedback"):
                status = (
                    "acknowledged"
                    if args.command == "ack-feedback"
                    else "resolved"
                )
                transition_feedback(
                    conn,
                    args.feedback_id,
                    status=status,
                    actor=args.actor,
                    detail=args.detail,
                )
                print(
                    json.dumps(
                        {"feedback_id": args.feedback_id, "status": status},
                        indent=2,
                    )
                )
            elif args.command in ("claim", "renew"):
                print(
                    json.dumps(
                        claim_task(
                            conn,
                            worker=args.worker,
                            task_id=args.task_id,
                            lease_minutes=args.minutes,
                            note=args.note,
                            require_existing=args.command == "renew",
                            random_assignment=(
                                args.command == "claim" and args.random
                            ),
                            random_seed=(
                                args.seed if args.command == "claim" else None
                            ),
                            priority_weighted_random=(
                                args.command == "claim"
                                and args.priority_weighted_random
                            ),
                        ),
                        indent=2,
                    )
                )
            elif args.command == "release":
                release_claim(
                    conn,
                    task_id=args.task_id,
                    worker=args.worker,
                    outcome=args.outcome,
                )
                print(
                    json.dumps(
                        {
                            "task_id": args.task_id,
                            "worker": args.worker,
                            "released": True,
                        },
                        indent=2,
                    )
                )
            elif args.command == "show":
                print(
                    json.dumps(
                        task_snapshot(conn, args.task_id),
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            elif args.command == "stats":
                with conn:
                    _purge_expired_claims(conn, actor="stats")
                print(json.dumps(database_stats(conn), indent=2))
            else:
                raise AssertionError(args.command)
    except CoordinationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
