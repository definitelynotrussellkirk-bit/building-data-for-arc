#!/usr/bin/env python3
"""Create disjoint, randomly assigned copies of the generator review bundle.

Each assignment is reserved through the live SQLite coordinator before its
copy is written.  The resulting archive contains an immutable
``2/ASSIGNMENT.json`` receipt.  This is the collision-safe way to distribute
``reviews/2.tar.zst`` to disconnected reviewers; copying the same unassigned
archive and letting every reviewer draw locally cannot guarantee uniqueness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import kimi_review_db  # noqa: E402
from scripts import bootstrap_random_generator_assignment as random_assignment  # noqa: E402


DEFAULT_SOURCE = ROOT / "reviews" / "2.tar.zst"
DEFAULT_OUTPUT_DIR = ROOT / "reviews" / "parallel_generator_workers"
ASSIGNMENT_MEMBER = "2/ASSIGNMENT.json"
WORKER_GUIDE_MEMBER = "2/CURRENT-GENERATOR-WORKER.md"
FEEDBACK_GUIDE_MEMBER = "2/FEEDBACK-LOOP.md"
RESULT_SCHEMA_MEMBER = "2/GENERATOR-RESULT-SCHEMA.json"
RESPONSE_SCHEMA_MEMBER = "2/CODEX-RESPONSE-SCHEMA.json"
ASSOCIATED_NOTES_MEMBER = (
    "2/repo/data/derived/generator_associated_notes.jsonl"
)


class BundleError(RuntimeError):
    """Raised when a distributable worker bundle cannot be built safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def current_commit(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def assignment_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            task_id = value.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise BundleError(f"{path}:{line_number}: invalid task_id")
            rows[task_id] = value
    return rows


def associated_note_rows(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            task_id = value.get("task_id") if isinstance(value, dict) else None
            if not isinstance(task_id, str) or not task_id:
                raise BundleError(f"{path}:{line_number}: invalid note task_id")
            rows.setdefault(task_id, []).append(value)
    return rows


def generator_member(row: dict[str, Any]) -> str:
    relative = row.get("path")
    if not isinstance(relative, str) or not relative:
        raise BundleError(f"{row.get('task_id')}: queue row has no path")
    return f"2/repo/{relative}"


def archive_kind(path: Path) -> str:
    if path.suffix == ".zip":
        return "zip"
    if path.name.endswith(".tar.zst"):
        return "tar.zst"
    raise BundleError(f"unsupported bundle archive: {path}")


def archive_names(path: Path) -> set[str]:
    if archive_kind(path) == "zip":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    result = subprocess.run(
        ["tar", "-I", "zstd", "-tf", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.rstrip("/") for line in result.stdout.splitlines()}


def archive_member_bytes(path: Path, member: str) -> bytes:
    if archive_kind(path) == "zip":
        try:
            with zipfile.ZipFile(path) as archive:
                return archive.read(member)
        except KeyError as exc:
            raise BundleError(
                f"{path} lacks assigned source {member}"
            ) from exc
    result = subprocess.run(
        ["tar", "-I", "zstd", "-xOf", str(path), member],
        capture_output=True,
    )
    if result.returncode != 0:
        raise BundleError(f"{path} lacks assigned source {member}")
    return result.stdout


def archive_member_sha256(path: Path, member: str) -> str:
    digest = hashlib.sha256()
    digest.update(archive_member_bytes(path, member))
    return digest.hexdigest()


def committed_task_authorities(
    task_id: str,
    root: Path = ROOT,
) -> dict[str, bytes]:
    """Return task-local base solution files exactly as stored in ``HEAD``."""
    base_root = root / "data" / "base" / "solutions"
    paths: list[Path] = []
    for path in sorted(base_root.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("task_id") == task_id:
            paths.append(path)
    attachments: dict[str, bytes] = {}
    for path in paths:
        relative = path.relative_to(root)
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative.as_posix()}"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        attachments[f"2/repo/{relative.as_posix()}"] = result.stdout
    return attachments


def build_manifest(
    *,
    batch_id: str,
    slot: int,
    source_archive: Path,
    source_archive_sha256: str,
    base_commit: str,
    queue_path: Path,
    queue_sha256: str,
    claims: list[dict[str, Any]],
    rows: dict[str, dict[str, Any]],
    notes: dict[str, list[dict[str, Any]]] | None = None,
    source_lineage: dict[str, list[dict[str, Any]]] | None = None,
    authorities: dict[str, dict[str, bytes]] | None = None,
    assignment_preflights: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    authorities = authorities or {}
    notes = notes or {}
    source_lineage = source_lineage or {}
    assignment_preflights = assignment_preflights or {}
    ontology_contract = random_assignment.skill_ontology_contract(ROOT)
    assignments = []
    for claim in claims:
        queue_row = rows[claim["task_id"]]
        row = random_assignment.merge_assignment_preflight(
            queue_row,
            assignment_preflights.get(claim["task_id"], {}),
        )
        task_authorities = authorities.get(claim["task_id"], {})
        if task_authorities:
            authority_mode = "task_local_base"
            authority_files = [
                {
                    "path": member,
                    "repo_relpath": member.removeprefix("2/repo/"),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
                for member, payload in sorted(task_authorities.items())
            ]
        elif row.get("kind") == "generic":
            generic_member = generator_member(row)
            authority_mode = "generic_embedded_program"
            authority_files = [
                {
                    "path": generic_member,
                    "repo_relpath": generic_member.removeprefix("2/repo/"),
                    "sha256": archive_member_sha256(
                        source_archive,
                        generic_member,
                    ),
                }
            ]
        else:
            canonical_member = "2/repo/data/canonical/puzzles.jsonl"
            authority_mode = "canonical_only"
            authority_files = [
                {
                    "path": canonical_member,
                    "repo_relpath": "data/canonical/puzzles.jsonl",
                    "sha256": archive_member_sha256(
                        source_archive,
                        canonical_member,
                    ),
                }
            ]
        assignments.append(
            {
                "task_id": claim["task_id"],
                "worker_id": claim["worker"],
                "claim_expires_at": claim["expires_at"],
                "selection_seed": claim["selection_seed"],
                "candidate_count": claim["candidate_count"],
                "selection_strategy": claim.get(
                    "selection_strategy", "uniform_random"
                ),
                "kind": row.get("kind"),
                "path": row.get("path"),
                "queue_rank": row.get("queue_rank"),
                "priority_score": row.get("priority_score"),
                "findings": row.get("findings") or [],
                "finding_taxonomy": row.get("finding_taxonomy") or {},
                "active_semantic_veto": bool(
                    row.get("active_semantic_veto")
                ),
                "rule_hash_expected": row.get("rule_hash_expected") or "",
                "generator_sha256": archive_member_sha256(
                    source_archive, generator_member(row)
                ),
                "queue_row_sha256": canonical_digest(queue_row),
                "assignment_checklist": row.get("assignment_checklist") or {},
                "assignment_preflight": row.get("assignment_preflight") or {},
                "associated_notes": notes.get(claim["task_id"], []),
                "known_source_lineage": source_lineage.get(
                    claim["task_id"], []
                ),
                "source_lineage_contract": {
                    "required": True,
                    "goal": "2-4 verified generator families per supplied ARC puzzle",
                    "result_field": "RESULTS.json.tasks[].source_lineage",
                    "raison_d_etre_required": True,
                    "skill_claims": [
                        "skills_taught",
                        "skills_exercised",
                        "skills_tested",
                    ],
                    "shortcut_probe_evidence_required": True,
                    "qwen_handoff_required": True,
                    "skill_ontology_contract": ontology_contract,
                },
                "authority_mode": authority_mode,
                "authority_files": authority_files,
            }
        )
    return {
        "schema_version": 1,
        "purpose": "external_generator_quality_worker",
        "batch_id": batch_id,
        "copy_id": f"{batch_id}-slot-{slot:03d}",
        "slot": slot,
        "base_commit": base_commit,
        "source_bundle": str(source_archive),
        "source_bundle_sha256": source_archive_sha256,
        "queue_source": str(queue_path),
        "queue_sha256": queue_sha256,
        "assignment_member": ASSIGNMENT_MEMBER,
        "worker_guide": WORKER_GUIDE_MEMBER,
        "authority_path_base": "bundle_root",
        "repository_member_root": "2/repo",
        "skill_ontology_contract": ontology_contract,
        "assignments": assignments,
        "return_policy": {
            "status_is_candidate_only": True,
            "independent_monitor_required_for_reviewed_safe": True,
            "echo_assignment_unchanged": True,
            "feedback_to_codex_required": True,
            "codex_response_supported": True,
            "source_lineage_required": True,
            "raison_d_etre_required": True,
            "skill_coverage_required": True,
            "qwen_lineage_handoff_required": True,
            "skill_ontology_reference_required": True,
            "candidate_skill_claims_do_not_count": True,
        },
        "feedback_channel": {
            "channel_id": f"{batch_id}-slot-{slot:03d}",
            "worker_to_codex": {
                "markdown_member": "FEEDBACK_TO_CODEX.md",
                "results_field": "feedback_to_codex",
                "schema_member": RESULT_SCHEMA_MEMBER,
            },
            "codex_to_worker": {
                "member": "CODEX-RESPONSE.json",
                "schema_member": RESPONSE_SCHEMA_MEMBER,
            },
            "protocol_member": FEEDBACK_GUIDE_MEMBER,
        },
    }


def write_assigned_copy(
    source_archive: Path,
    destination: Path,
    manifest: dict[str, Any],
    attachments: dict[str, bytes] | None = None,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise BundleError(f"refusing to overwrite {destination}")
    if archive_kind(source_archive) == "zip":
        shutil.copy2(source_archive, destination)
        with zipfile.ZipFile(
            destination,
            "a",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            names = set(archive.namelist())
            _validate_worker_members(names)
            for member, payload in sorted((attachments or {}).items()):
                if member in names:
                    if archive.read(member) != payload:
                        raise BundleError(
                            f"source archive has stale attachment {member}"
                        )
                    continue
                archive.writestr(member, payload)
            archive.writestr(
                ASSIGNMENT_MEMBER,
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            )
        return

    with tempfile.TemporaryDirectory(
        prefix="arc-generator-worker-"
    ) as directory:
        extracted = Path(directory)
        subprocess.run(
            [
                "tar",
                "-I",
                "zstd",
                "-xf",
                str(source_archive),
                "-C",
                str(extracted),
            ],
            check=True,
        )
        names = {
            path.relative_to(extracted).as_posix()
            for path in extracted.rglob("*")
            if path.is_file()
        }
        _validate_worker_members(names)
        for member, payload in sorted((attachments or {}).items()):
            target = extracted / member
            if target.is_file():
                if target.read_bytes() != payload:
                    raise BundleError(
                        f"source archive has stale attachment {member}"
                    )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        assignment = extracted / ASSIGNMENT_MEMBER
        assignment.parent.mkdir(parents=True, exist_ok=True)
        assignment.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "tar",
                "-I",
                "zstd -T0 -10",
                "-cf",
                str(destination),
                "-C",
                str(extracted),
                "2",
            ],
            check=True,
        )


def _validate_worker_members(names: set[str]) -> None:
    required_members = {
        WORKER_GUIDE_MEMBER,
        FEEDBACK_GUIDE_MEMBER,
        RESULT_SCHEMA_MEMBER,
        RESPONSE_SCHEMA_MEMBER,
    }
    missing_members = sorted(required_members - names)
    if missing_members:
        raise BundleError(
            "source archive lacks required worker interface member(s): "
            + ", ".join(missing_members)
        )
    if ASSIGNMENT_MEMBER in names:
        raise BundleError(
            f"source archive is already assigned ({ASSIGNMENT_MEMBER})"
        )


def release_reserved(
    conn: Any,
    reservations: list[dict[str, Any]],
    *,
    outcome: str,
) -> None:
    for claim in reversed(reservations):
        try:
            kimi_review_db.release_claim(
                conn,
                task_id=claim["task_id"],
                worker=claim["worker"],
                outcome=outcome,
            )
        except Exception as exc:  # preserve the original bundle failure
            print(
                f"WARNING: could not release {claim['task_id']}: {exc}",
                file=sys.stderr,
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-archive",
        "--source-zip",
        dest="source_archive",
        type=Path,
        default=DEFAULT_SOURCE,
        help="unassigned .tar.zst packet (.zip remains supported)",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--copies", type=int, required=True)
    parser.add_argument("--tasks-per-copy", type=int, default=1)
    parser.add_argument("--lease-minutes", type=int, default=24 * 60)
    parser.add_argument("--batch-id")
    parser.add_argument("--worker-prefix", default="external-generator")
    parser.add_argument("--db", type=Path, default=kimi_review_db.DEFAULT_DB)
    parser.add_argument(
        "--assignments",
        type=Path,
        default=kimi_review_db.DEFAULT_ASSIGNMENTS,
    )
    parser.add_argument(
        "--associated-notes",
        type=Path,
        default=ROOT / "data/derived/generator_associated_notes.jsonl",
    )
    parser.add_argument(
        "--source-lineage",
        type=Path,
        default=ROOT / "data/derived/official_generator_lineage.jsonl",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="seed for the first claim; later claims use seed+offset",
    )
    parser.add_argument(
        "--uniform-random",
        action="store_true",
        help=(
            "disable the default priority-weighted random draw; every "
            "pending task remains eligible in either mode"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.copies < 1:
        raise SystemExit("--copies must be positive")
    if not 1 <= args.tasks_per_copy <= 3:
        raise SystemExit("--tasks-per-copy must be 1..3 (one is recommended)")
    if not args.source_archive.is_file():
        raise SystemExit(f"missing source archive: {args.source_archive}")

    batch_id = args.batch_id or uuid.uuid4().hex[:12]
    source_sha = sha256_file(args.source_archive)
    queue_sha = sha256_file(args.assignments)
    rows = assignment_rows(args.assignments)
    notes = associated_note_rows(args.associated_notes)
    source_lineage = random_assignment.load_source_lineage(args.source_lineage)
    base_commit = current_commit()
    reservations: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []

    try:
        with kimi_review_db.connect_db(args.db) as conn:
            kimi_review_db.sync_sources(
                conn,
                reviews_path=kimi_review_db.DEFAULT_REVIEWS,
                assignments_path=args.assignments,
                vetoes_path=kimi_review_db.DEFAULT_VETOES,
                monitor_state_path=kimi_review_db.DEFAULT_MONITOR_STATE,
            )
            for slot in range(1, args.copies + 1):
                slot_claims = []
                for task_offset in range(args.tasks_per_copy):
                    claim_offset = len(reservations)
                    worker = (
                        f"{args.worker_prefix}:{batch_id}:slot-{slot:03d}:"
                        f"task-{task_offset + 1:02d}"
                    )
                    claim = kimi_review_db.claim_task(
                        conn,
                        worker=worker,
                        task_id=None,
                        lease_minutes=args.lease_minutes,
                        note=f"reserved for review bundle {batch_id}",
                        random_assignment=True,
                        random_seed=(
                            args.seed + claim_offset
                            if args.seed is not None
                            else None
                        ),
                        priority_weighted_random=not args.uniform_random,
                    )
                    if claim["task_id"] not in rows:
                        raise BundleError(
                            f"claimed task absent from queue snapshot: {claim['task_id']}"
                        )
                    reservations.append(claim)
                    slot_claims.append(claim)

                slot_authorities = {
                    claim["task_id"]: committed_task_authorities(
                        claim["task_id"]
                    )
                    for claim in slot_claims
                }
                slot_preflights = {
                    claim["task_id"]: (
                        random_assignment.fresh_assignment_preflight(
                            ROOT,
                            rows[claim["task_id"]],
                        )
                    )
                    for claim in slot_claims
                }
                manifest = build_manifest(
                    batch_id=batch_id,
                    slot=slot,
                    source_archive=args.source_archive,
                    source_archive_sha256=source_sha,
                    base_commit=base_commit,
                    queue_path=args.assignments,
                    queue_sha256=queue_sha,
                    claims=slot_claims,
                    rows=rows,
                    notes=notes,
                    source_lineage=source_lineage,
                    authorities=slot_authorities,
                    assignment_preflights=slot_preflights,
                )
                attachments = {
                    member: payload
                    for task_attachments in slot_authorities.values()
                    for member, payload in task_attachments.items()
                }
                # Freeze the exact ontology named by the assignment receipt into
                # every worker copy, even when the reusable source packet predates it.
                attachments["2/repo/data/skill_ontology.json"] = (
                    ROOT / "data/skill_ontology.json"
                ).read_bytes()
                suffix = (
                    ".zip"
                    if archive_kind(args.source_archive) == "zip"
                    else ".tar.zst"
                )
                destination = args.output_dir / (
                    f"2_generator_worker_{batch_id}_slot_{slot:03d}{suffix}"
                )
                write_assigned_copy(
                    args.source_archive,
                    destination,
                    manifest,
                    attachments,
                )
                outputs.append(
                    {
                        "path": str(destination),
                        "sha256": sha256_file(destination),
                        "task_ids": [c["task_id"] for c in slot_claims],
                        "workers": [c["worker"] for c in slot_claims],
                    }
                )
    except Exception:
        if reservations:
            with kimi_review_db.connect_db(args.db) as conn:
                release_reserved(
                    conn,
                    reservations,
                    outcome=f"bundle build {batch_id} failed",
                )
        raise

    print(
        json.dumps(
            {
                "batch_id": batch_id,
                "base_commit": base_commit,
                "source_bundle_sha256": source_sha,
                "copies": outputs,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
