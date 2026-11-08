#!/usr/bin/env python3
"""Ingest external generator-worker feedback and export Codex responses.

The assigned review bundles are intentionally disconnected from the live
coordination database.  Workers return structured ``feedback_to_codex`` items
inside RESULTS.json.  This tool gives those items durable IDs, exposes an inbox,
records Codex dispositions, and exports a response packet that can be sent back
to the worker without editing their immutable assignment receipt.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "tmp/kimi_swarm/review_coordination.sqlite3"
DISPOSITIONS = {
    "acknowledged",
    "accepted",
    "implemented",
    "needs_evidence",
    "declined",
    "deferred",
}
NOTE_CATEGORIES = {
    "design_decision",
    "rejected_hypothesis",
    "known_limitation",
    "future_check",
    "source_sync",
    "tooling",
    "other",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    initialize(connection)
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_worker_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest TEXT NOT NULL UNIQUE,
            assignment_copy_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            local_id TEXT NOT NULL,
            task_id TEXT,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            summary TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            suggested_action TEXT NOT NULL,
            confidence TEXT NOT NULL,
            response_requested INTEGER NOT NULL,
            blocks_completion INTEGER NOT NULL,
            received_at TEXT NOT NULL,
            source_results TEXT NOT NULL,
            disposition TEXT,
            response_message TEXT,
            response_evidence_json TEXT,
            responded_at TEXT,
            responded_by TEXT,
            UNIQUE(assignment_copy_id, local_id)
        );
        CREATE INDEX IF NOT EXISTS external_worker_feedback_inbox
            ON external_worker_feedback(disposition, severity, received_at);

        CREATE TABLE IF NOT EXISTS generator_associated_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest TEXT NOT NULL UNIQUE,
            task_id TEXT NOT NULL,
            note_key TEXT NOT NULL,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            rationale TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            future_check TEXT NOT NULL,
            assignment_copy_id TEXT,
            worker_id TEXT NOT NULL,
            source_results TEXT NOT NULL,
            created_at TEXT NOT NULL,
            supersedes_id INTEGER,
            is_current INTEGER NOT NULL CHECK(is_current IN (0, 1)),
            FOREIGN KEY(supersedes_id) REFERENCES generator_associated_notes(id)
        );
        CREATE INDEX IF NOT EXISTS generator_associated_notes_current
            ON generator_associated_notes(task_id, is_current, note_key, id);
        """
    )
    connection.commit()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected one JSON object")
    return value


def _feedback_digest(copy_id: str, worker_id: str, item: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "assignment_copy_id": copy_id,
            "worker_id": worker_id,
            "item": item,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_feedback(results: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    copy_id = results.get("assignment_copy_id")
    worker_id = results.get("worker_id")
    feedback = results.get("feedback_to_codex")
    if not isinstance(copy_id, str) or not copy_id:
        raise ValueError("RESULTS.json: assignment_copy_id must be nonempty")
    if not isinstance(worker_id, str) or not worker_id:
        raise ValueError("RESULTS.json: worker_id must be nonempty")
    if not isinstance(feedback, dict):
        raise ValueError("RESULTS.json: feedback_to_codex must be an object")
    items = feedback.get("items")
    if not isinstance(items, list):
        raise ValueError("RESULTS.json: feedback_to_codex.items must be a list")
    seen: set[str] = set()
    normalized = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"feedback item {index}: expected object")
        local_id = item.get("local_id")
        if not isinstance(local_id, str) or not local_id:
            raise ValueError(f"feedback item {index}: local_id must be nonempty")
        if local_id in seen:
            raise ValueError(f"feedback item {index}: duplicate local_id {local_id!r}")
        seen.add(local_id)
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(value, str) and value.strip() for value in evidence
        ):
            raise ValueError(f"feedback item {local_id}: evidence must be a string list")
        normalized.append(
            {
                "local_id": local_id,
                "task_id": str(item.get("task_id") or ""),
                "category": str(item.get("category") or "other"),
                "severity": str(item.get("severity") or "suggestion"),
                "summary": str(item.get("summary") or "").strip(),
                "evidence": evidence,
                "suggested_action": str(item.get("suggested_action") or "").strip(),
                "confidence": str(item.get("confidence") or "medium"),
                "response_requested": bool(item.get("response_requested")),
                "blocks_completion": bool(item.get("blocks_completion")),
            }
        )
        if not normalized[-1]["summary"]:
            raise ValueError(f"feedback item {local_id}: summary must be nonempty")
    return copy_id, worker_id, normalized


def _validate_associated_notes(
    results: dict[str, Any],
    assigned_tasks: set[str],
) -> list[dict[str, Any]]:
    """Normalize task-local notes while preserving compatibility with old returns."""
    normalized = []
    for task_index, task in enumerate(results.get("tasks") or []):
        if not isinstance(task, dict):
            raise ValueError(f"task result {task_index}: expected object")
        task_id = str(task.get("task_id") or "")
        if not task_id:
            raise ValueError(f"task result {task_index}: task_id must be nonempty")
        if task_id not in assigned_tasks:
            raise ValueError(
                f"task result {task_index}: task {task_id} is not in ASSIGNMENT.json"
            )
        notes = task.get("associated_notes")
        if notes is None:
            # Version-2 returns created before this channel remain ingestible.
            continue
        if not isinstance(notes, list):
            raise ValueError(
                f"task {task_id}: associated_notes must be a list"
            )
        seen = set()
        for note_index, note in enumerate(notes):
            if not isinstance(note, dict):
                raise ValueError(
                    f"task {task_id} note {note_index}: expected object"
                )
            note_key = str(note.get("note_key") or "").strip()
            if not note_key or not all(
                char.islower() or char.isdigit() or char in "_-"
                for char in note_key
            ):
                raise ValueError(
                    f"task {task_id} note {note_index}: note_key must use "
                    "lowercase letters, digits, underscores, or hyphens"
                )
            if note_key in seen:
                raise ValueError(
                    f"task {task_id}: duplicate associated note key {note_key!r}"
                )
            seen.add(note_key)
            category = str(note.get("category") or "other")
            if category not in NOTE_CATEGORIES:
                raise ValueError(
                    f"task {task_id} note {note_key}: unknown category "
                    f"{category!r}"
                )
            summary = str(note.get("summary") or "").strip()
            rationale = str(note.get("rationale") or "").strip()
            future_check = str(note.get("future_check") or "").strip()
            evidence = note.get("evidence")
            if not summary or not rationale or not future_check:
                raise ValueError(
                    f"task {task_id} note {note_key}: summary, rationale, "
                    "and future_check must be nonempty"
                )
            if not isinstance(evidence, list) or not all(
                isinstance(value, str) and value.strip() for value in evidence
            ):
                raise ValueError(
                    f"task {task_id} note {note_key}: evidence must be a "
                    "nonempty-string list"
                )
            normalized.append(
                {
                    "task_id": task_id,
                    "note_key": note_key,
                    "category": category,
                    "summary": summary,
                    "rationale": rationale,
                    "evidence": evidence,
                    "future_check": future_check,
                }
            )
    return normalized


def _note_digest(note: dict[str, Any]) -> str:
    payload = json.dumps(
        note,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def store_associated_note(
    connection: sqlite3.Connection,
    note: dict[str, Any],
    *,
    worker_id: str,
    source_results: str,
    assignment_copy_id: str | None = None,
) -> tuple[str, bool]:
    """Append one note version and supersede the previous version of its key."""
    digest = _note_digest(note)
    existing = connection.execute(
        "SELECT id FROM generator_associated_notes WHERE digest = ?",
        (digest,),
    ).fetchone()
    if existing:
        return f"GNOTE-{int(existing['id']):06d}", False
    previous = connection.execute(
        """
        SELECT id FROM generator_associated_notes
        WHERE task_id = ? AND note_key = ? AND is_current = 1
        ORDER BY id DESC LIMIT 1
        """,
        (note["task_id"], note["note_key"]),
    ).fetchone()
    previous_id = int(previous["id"]) if previous else None
    if previous_id is not None:
        connection.execute(
            "UPDATE generator_associated_notes SET is_current = 0 WHERE id = ?",
            (previous_id,),
        )
    cursor = connection.execute(
        """
        INSERT INTO generator_associated_notes (
            digest, task_id, note_key, category, summary, rationale,
            evidence_json, future_check, assignment_copy_id, worker_id,
            source_results, created_at, supersedes_id, is_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            digest,
            note["task_id"],
            note["note_key"],
            note["category"],
            note["summary"],
            note["rationale"],
            json.dumps(note["evidence"], ensure_ascii=False),
            note["future_check"],
            assignment_copy_id,
            worker_id,
            source_results,
            utc_now(),
            previous_id,
        ),
    )
    return f"GNOTE-{int(cursor.lastrowid):06d}", True


def associated_notes(
    db_path: Path = DEFAULT_DB,
    *,
    task_id: str | None = None,
    include_history: bool = False,
) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        clauses = []
        params: list[Any] = []
        if task_id:
            clauses.append("task_id = ?")
            params.append(task_id)
        if not include_history:
            clauses.append("is_current = 1")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            f"""
            SELECT * FROM generator_associated_notes
            {where}
            ORDER BY task_id, note_key, id
            """,
            params,
        ).fetchall()
    result = []
    for raw in rows:
        row = dict(raw)
        row["note_id"] = f"GNOTE-{int(row.pop('id')):06d}"
        row["supersedes_note_id"] = (
            f"GNOTE-{int(row.pop('supersedes_id')):06d}"
            if row["supersedes_id"] is not None
            else None
        )
        row["evidence"] = json.loads(row.pop("evidence_json"))
        row["is_current"] = bool(row["is_current"])
        result.append(row)
    return result


def backfill_associated_notes(
    reviews_path: Path,
    *,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:
    """Seed one maintained rationale note from each task's latest review."""
    latest: dict[str, dict[str, Any]] = {}
    with reviews_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict) or not value.get("task_id"):
                raise ValueError(
                    f"{reviews_path}:{line_number}: expected review object "
                    "with task_id"
                )
            latest[str(value["task_id"])] = value

    inserted = []
    existing = []
    with connect(db_path) as connection:
        for task_id, review in sorted(latest.items()):
            semantic_rule = str(review.get("semantic_rule") or "").strip()
            if not semantic_rule:
                continue
            changes = review.get("generator_changes")
            if isinstance(changes, list):
                rationale = "; ".join(str(item) for item in changes if item)
            else:
                rationale = str(changes or "").strip()
            if not rationale:
                rationale = (
                    "Backfilled from the latest accepted review; preserve this "
                    "semantic interpretation unless new canonical evidence "
                    "contradicts it."
                )
            warnings = review.get("warnings_disposition")
            if isinstance(warnings, list):
                future_check = "; ".join(str(item) for item in warnings if item)
            else:
                future_check = str(warnings or "").strip()
            if not future_check:
                future_check = (
                    "Re-run the independent monitor after any generator or "
                    "Racket authority change."
                )
            after = review.get("after")
            after = after if isinstance(after, dict) else {}
            evidence = [
                f"review status={review.get('status', 'unknown')}",
                f"reviewed_at={review.get('reviewed_at', 'unknown')}",
                "accepted source="
                f"{after.get('source_hash') or after.get('generator_sha256') or review.get('generator_snapshot_sha256') or 'unknown'}",
            ]
            note = {
                "task_id": task_id,
                "note_key": "accepted_semantic_rule",
                "category": "design_decision",
                "summary": semantic_rule,
                "rationale": rationale,
                "evidence": evidence,
                "future_check": future_check,
            }
            note_id, was_inserted = store_associated_note(
                connection,
                note,
                worker_id="codex:review-ledger-backfill",
                source_results=str(reviews_path),
            )
            (inserted if was_inserted else existing).append(note_id)
            for explicit in review.get("associated_notes") or []:
                if not isinstance(explicit, dict):
                    continue
                normalized = dict(explicit)
                normalized["task_id"] = task_id
                # Validate explicit notes through the same strict normalizer
                # used for disconnected worker returns.
                checked = _validate_associated_notes(
                    {
                        "tasks": [
                            {
                                "task_id": task_id,
                                "associated_notes": [normalized],
                            }
                        ]
                    },
                    {task_id},
                )[0]
                explicit_id, explicit_inserted = store_associated_note(
                    connection,
                    checked,
                    worker_id=str(review.get("reviewer") or "codex"),
                    source_results=str(reviews_path),
                )
                (
                    inserted if explicit_inserted else existing
                ).append(explicit_id)
        connection.commit()
    return {
        "review_tasks": len(latest),
        "notes_inserted": inserted,
        "notes_existing": existing,
    }


def export_associated_notes(
    output: Path,
    *,
    db_path: Path = DEFAULT_DB,
    include_history: bool = False,
) -> dict[str, Any]:
    rows = associated_notes(
        db_path,
        include_history=include_history,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )
    temporary.replace(output)
    return {
        "output": str(output),
        "notes": len(rows),
        "include_history": include_history,
    }


def ingest_response(
    results_path: Path,
    assignment_path: Path,
    *,
    db_path: Path = DEFAULT_DB,
    allow_out_of_scope: bool = False,
) -> dict[str, Any]:
    results = _load_object(results_path)
    assignment = _load_object(assignment_path)
    copy_id, worker_id, items = _validate_feedback(results)
    if assignment.get("copy_id") != copy_id:
        raise ValueError(
            "assignment_copy_id does not match immutable ASSIGNMENT.json copy_id"
        )
    assigned_tasks = {
        str(item.get("task_id"))
        for item in assignment.get("assignments") or []
        if isinstance(item, dict) and item.get("task_id")
    }
    out_of_scope = [
        item
        for item in items
        if item["task_id"] and item["task_id"] not in assigned_tasks
    ]
    if out_of_scope and not allow_out_of_scope:
        item = out_of_scope[0]
        raise ValueError(
            f"feedback {item['local_id']}: task {item['task_id']} "
            "is not in ASSIGNMENT.json"
        )
    if out_of_scope:
        items = [item for item in items if item not in out_of_scope]
    notes = _validate_associated_notes(results, assigned_tasks)
    inserted = []
    existing = []
    notes_inserted = []
    notes_existing = []
    with connect(db_path) as connection:
        for item in items:
            digest = _feedback_digest(copy_id, worker_id, item)
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO external_worker_feedback (
                    digest, assignment_copy_id, worker_id, local_id, task_id,
                    category, severity, summary, evidence_json,
                    suggested_action, confidence, response_requested,
                    blocks_completion, received_at, source_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    digest,
                    copy_id,
                    worker_id,
                    item["local_id"],
                    item["task_id"] or None,
                    item["category"],
                    item["severity"],
                    item["summary"],
                    json.dumps(item["evidence"], ensure_ascii=False),
                    item["suggested_action"],
                    item["confidence"],
                    int(item["response_requested"]),
                    int(item["blocks_completion"]),
                    utc_now(),
                    str(results_path),
                ),
            )
            row = connection.execute(
                "SELECT id FROM external_worker_feedback WHERE digest = ?",
                (digest,),
            ).fetchone()
            public_id = f"EWF-{int(row['id']):06d}"
            (inserted if cursor.rowcount else existing).append(public_id)
        for note in notes:
            note_id, was_inserted = store_associated_note(
                connection,
                note,
                worker_id=worker_id,
                source_results=str(results_path),
                assignment_copy_id=copy_id,
            )
            (notes_inserted if was_inserted else notes_existing).append(note_id)
        connection.commit()
    return {
        "assignment_copy_id": copy_id,
        "worker_id": worker_id,
        "feedback_items": len(items),
        "inserted": inserted,
        "existing": existing,
        "associated_notes": len(notes),
        "notes_inserted": notes_inserted,
        "notes_existing": notes_existing,
        "out_of_scope": [
            {
                "local_id": item["local_id"],
                "task_id": item["task_id"],
                "summary": item["summary"],
            }
            for item in out_of_scope
        ],
    }


def inbox(db_path: Path = DEFAULT_DB, *, include_responded: bool = False) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        clause = "" if include_responded else "WHERE disposition IS NULL"
        rows = connection.execute(
            f"""
            SELECT * FROM external_worker_feedback
            {clause}
            ORDER BY blocks_completion DESC, response_requested DESC,
                     CASE severity
                         WHEN 'blocker' THEN 0
                         WHEN 'warning' THEN 1
                         WHEN 'suggestion' THEN 2
                         ELSE 3
                     END,
                     id
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["feedback_id"] = f"EWF-{int(value.pop('id')):06d}"
    value["evidence"] = json.loads(value.pop("evidence_json"))
    raw_response = value.pop("response_evidence_json")
    value["response_evidence"] = json.loads(raw_response) if raw_response else []
    value["response_requested"] = bool(value["response_requested"])
    value["blocks_completion"] = bool(value["blocks_completion"])
    return value


def _parse_feedback_id(feedback_id: str) -> int:
    if not feedback_id.startswith("EWF-") or not feedback_id[4:].isdigit():
        raise ValueError("feedback id must look like EWF-000001")
    return int(feedback_id[4:])


def respond(
    feedback_id: str,
    *,
    disposition: str,
    message: str,
    evidence: list[str] | None = None,
    responded_by: str = "codex",
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:
    if disposition not in DISPOSITIONS:
        raise ValueError(f"unknown disposition {disposition!r}")
    if not message.strip():
        raise ValueError("response message must be nonempty")
    row_id = _parse_feedback_id(feedback_id)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE external_worker_feedback
            SET disposition = ?, response_message = ?,
                response_evidence_json = ?, responded_at = ?, responded_by = ?
            WHERE id = ?
            """,
            (
                disposition,
                message.strip(),
                json.dumps(evidence or [], ensure_ascii=False),
                utc_now(),
                responded_by,
                row_id,
            ),
        )
        if cursor.rowcount != 1:
            raise KeyError(feedback_id)
        connection.commit()
        row = connection.execute(
            "SELECT * FROM external_worker_feedback WHERE id = ?",
            (row_id,),
        ).fetchone()
    return _row_to_dict(row)


def export_responses(
    assignment_copy_id: str,
    output: Path,
    *,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM external_worker_feedback
            WHERE assignment_copy_id = ? AND disposition IS NOT NULL
            ORDER BY id
            """,
            (assignment_copy_id,),
        ).fetchall()
    responses = []
    for raw in rows:
        row = _row_to_dict(raw)
        responses.append(
            {
                "feedback_id": row["feedback_id"],
                "local_id": row["local_id"],
                "task_id": row["task_id"] or "",
                "disposition": row["disposition"],
                "message": row["response_message"],
                "evidence": row["response_evidence"],
                "responded_at": row["responded_at"],
                "responded_by": row["responded_by"],
            }
        )
    payload = {
        "schema_version": 1,
        "assignment_copy_id": assignment_copy_id,
        "generated_at": utc_now(),
        "responses": responses,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("results", type=Path)
    ingest_parser.add_argument("--assignment", type=Path, required=True)

    inbox_parser = subparsers.add_parser("inbox")
    inbox_parser.add_argument("--all", action="store_true")

    respond_parser = subparsers.add_parser("respond")
    respond_parser.add_argument("feedback_id")
    respond_parser.add_argument("--disposition", choices=sorted(DISPOSITIONS), required=True)
    respond_parser.add_argument("--message", required=True)
    respond_parser.add_argument("--evidence", action="append", default=[])
    respond_parser.add_argument("--responded-by", default="codex")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("assignment_copy_id")
    export_parser.add_argument("--out", type=Path, required=True)

    notes_parser = subparsers.add_parser(
        "notes", help="list current associated notes for one or all generators"
    )
    notes_parser.add_argument("--task-id")
    notes_parser.add_argument("--history", action="store_true")

    backfill_parser = subparsers.add_parser(
        "backfill-notes",
        help="derive maintained notes from the latest accepted review per task",
    )
    backfill_parser.add_argument("--reviews", type=Path, required=True)
    backfill_parser.add_argument("--out", type=Path)

    export_notes_parser = subparsers.add_parser(
        "export-notes", help="export associated notes as JSONL"
    )
    export_notes_parser.add_argument("--out", type=Path, required=True)
    export_notes_parser.add_argument("--history", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "ingest":
        value = ingest_response(args.results, args.assignment, db_path=args.db)
    elif args.command == "inbox":
        value = inbox(args.db, include_responded=args.all)
    elif args.command == "respond":
        value = respond(
            args.feedback_id,
            disposition=args.disposition,
            message=args.message,
            evidence=args.evidence,
            responded_by=args.responded_by,
            db_path=args.db,
        )
    elif args.command == "export":
        value = export_responses(
            args.assignment_copy_id,
            args.out,
            db_path=args.db,
        )
    elif args.command == "notes":
        value = associated_notes(
            args.db,
            task_id=args.task_id,
            include_history=args.history,
        )
    elif args.command == "backfill-notes":
        value = backfill_associated_notes(
            args.reviews,
            db_path=args.db,
        )
        if args.out:
            value["export"] = export_associated_notes(
                args.out,
                db_path=args.db,
            )
    else:
        value = export_associated_notes(
            args.out,
            db_path=args.db,
            include_history=args.history,
        )
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
