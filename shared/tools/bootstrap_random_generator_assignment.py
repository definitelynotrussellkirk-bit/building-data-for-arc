#!/usr/bin/env python3
"""Create one stable random generator assignment inside an extracted bundle.

This is the disconnected fallback for reviewers who receive the base
``reviews/2.tar.zst`` instead of a centrally reserved worker copy. It chooses
from the bundled pending queue with OS randomness and writes ``ASSIGNMENT.json``
exactly once.  Separate disconnected copies cannot make a strict no-collision
guarantee; use ``make_parallel_generator_review_bundles.py`` before distribution
when the sender can access the live coordination database.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import math
import sys
import uuid
from typing import Any

SCRIPT_REPO = Path(__file__).resolve().parents[1]
if str(SCRIPT_REPO) not in sys.path:
    sys.path.insert(0, str(SCRIPT_REPO))


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




def skill_ontology_contract_from_value(ontology: dict[str, Any], *, path: str) -> dict[str, Any]:
    """Freeze the ontology contract copied into assignment receipts."""
    return {
        "schema_version": 1,
        "path": path,
        "ontology_id": ontology["ontology_id"],
        "ontology_version": ontology["ontology_version"],
        "ontology_sha256": canonical_digest(ontology),
        "allowed_skill_ids": sorted(
            row["skill_id"] for row in ontology.get("skills") or []
        ),
        "countable_skill_ids": sorted(
            row["skill_id"]
            for row in ontology.get("skills") or []
            if row.get("definition_status") == "verified"
        ),
        "allowed_shortcut_probe_type_ids": sorted(
            row["probe_type_id"]
            for row in ontology.get("shortcut_probe_types") or []
        ),
        "claim_statuses": ["verified", "candidate", "rejected"],
        "candidate_claims_do_not_count": True,
        "taught_exercised_tested_are_distinct": True,
        "tested_promotion_requires": [
            "semantic_witness_and_rival_verified",
            "tested_subset_of_verified_taught",
            "structured_shortcut_probes",
            "evidence_paths",
        ],
        "generator_skill_matrix": (
            "data/derived/official_generator_skill_matrix.jsonl"
        ),
    }


def skill_ontology_contract(repo: Path) -> dict[str, Any]:
    path = repo / "data/skill_ontology.json"
    distribution_status = "present_in_assignment_repo"
    if not path.is_file():
        # Small unit-test/minimal packet fixtures may omit data authorities. The
        # full contract is still frozen into ASSIGNMENT.json, and production
        # parallel bundles attach this exact file before distribution.
        path = SCRIPT_REPO / "data/skill_ontology.json"
        distribution_status = "embedded_contract_fallback"
    ontology = json.loads(path.read_text(encoding="utf-8"))
    contract = skill_ontology_contract_from_value(
        ontology, path="data/skill_ontology.json"
    )
    contract["distribution_status"] = distribution_status
    return contract


def load_candidates(path: Path, *, repo: Path | None = None) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            task_id = row.get("task_id")
            generator_path = row.get("path")
            if not isinstance(task_id, str) or not task_id:
                raise ValueError(f"{path}:{line_number}: invalid task_id")
            if not isinstance(generator_path, str) or not generator_path:
                raise ValueError(f"{path}:{line_number}: invalid path")
            if (
                row.get("status") == "pending"
                and row.get("train_safety") != "reviewed_safe"
                and (
                    repo is None
                    or (repo / generator_path).is_file()
                )
            ):
                candidates.append(row)
    if not candidates:
        raise ValueError(f"{path}: no eligible pending generators")
    return candidates


def load_returned_task_ids(path: Path) -> set[str]:
    """Return task IDs that already have a candidate repair at intake.

    Disconnected workers cannot coordinate live reservations, but the packet
    does contain a snapshot of accepted candidate returns.  Excluding those
    tasks prevents the most common avoidable duplicate: assigning work that
    has already made it back to the repository.
    """
    task_ids: set[str] = set()
    if not path.is_file():
        return task_ids
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row.get("task_id") if isinstance(row, dict) else None
            if not isinstance(task_id, str) or not task_id:
                raise ValueError(f"{path}:{line_number}: invalid task_id")
            task_ids.add(task_id)
    return task_ids


def avoid_returned_repairs(
    candidates: list[dict[str, Any]],
    returned_task_ids: set[str],
) -> tuple[list[dict[str, Any]], int, bool]:
    """Exclude prior returns when possible, with a loud exhaustion fallback."""
    fresh = [
        row for row in candidates
        if str(row.get("task_id") or "") not in returned_task_ids
    ]
    excluded = len(candidates) - len(fresh)
    if fresh:
        return fresh, excluded, False
    return candidates, excluded, bool(candidates and excluded)


def load_associated_notes(path: Path) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    if not path.is_file():
        return result
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row.get("task_id") if isinstance(row, dict) else None
            if not isinstance(task_id, str) or not task_id:
                raise ValueError(f"{path}:{line_number}: invalid note task_id")
            result.setdefault(task_id, []).append(row)
    return result


def load_source_lineage(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Index official-source lineage rows by generator ID."""
    result: dict[str, list[dict[str, Any]]] = {}
    if not path.is_file():
        return result
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            generator_id = (
                row.get("generator_id") if isinstance(row, dict) else None
            )
            if not isinstance(generator_id, str) or not generator_id:
                raise ValueError(
                    f"{path}:{line_number}: invalid generator_id"
                )
            result.setdefault(generator_id, []).append(row)
    return result


def fresh_assignment_preflight(
    repo: Path,
    row: dict[str, Any],
) -> dict[str, Any]:
    """Recheck the selected task so a stale queue cache cannot hide risk."""
    if repo != SCRIPT_REPO or row.get("kind") != "per_puzzle":
        return {}
    from scripts.build_kimi_generator_assignment import (
        _canonical_selfcheck_probe,
    )

    return _canonical_selfcheck_probe(
        str(row["task_id"]),
        repo / str(row["path"]),
    )


def merge_assignment_preflight(
    row: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    """Merge fresh selected-task findings into an immutable receipt row."""
    if not preflight:
        return row
    from scripts.build_kimi_generator_assignment import preflight_findings

    merged = dict(row)
    findings = list(row.get("findings") or [])
    fresh = preflight_findings(preflight)
    for finding in fresh:
        if finding not in findings:
            findings.append(finding)
    merged["findings"] = findings

    taxonomy = {
        key: list(value)
        for key, value in (row.get("finding_taxonomy") or {}).items()
    }
    semantic = taxonomy.setdefault("generator_oracle_semantics", [])
    for finding in fresh:
        if finding not in semantic:
            semantic.append(finding)
    taxonomy.setdefault("source_authority", [])
    merged["finding_taxonomy"] = taxonomy

    checklist = dict(row.get("assignment_checklist") or {})
    repair_focus = list(checklist.get("repair_focus") or [])
    for finding in fresh:
        item = f"resolve:{finding}"
        if item not in repair_focus:
            repair_focus.append(item)
    checklist["repair_focus"] = repair_focus
    merged["assignment_checklist"] = checklist
    merged["assignment_preflight"] = preflight
    return merged


def task_authorities(
    repo: Path,
    task_id: str,
    *,
    kind: str = "",
    generator_path: Path | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Return exact bundled authority paths and hashes for one assignment."""
    if kind == "generic":
        if generator_path is None or not generator_path.is_file():
            raise SystemExit(
                f"missing generic embedded-program authority for {task_id}"
            )
        return (
            "generic_embedded_program",
            [
                {
                    "path": (
                        "2/repo/"
                        + generator_path.relative_to(repo).as_posix()
                    ),
                    "repo_relpath": generator_path.relative_to(repo).as_posix(),
                    "sha256": sha256_file(generator_path),
                }
            ],
        )

    base_root = repo / "data/base/solutions"
    base_paths: list[Path] = []
    if base_root.is_dir():
        for path in sorted(base_root.rglob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("task_id") == task_id:
                base_paths.append(path)
    if base_paths:
        return (
            "task_local_base",
            [
                {
                    "path": (
                        "2/repo/"
                        + path.relative_to(repo).as_posix()
                    ),
                    "repo_relpath": path.relative_to(repo).as_posix(),
                    "sha256": sha256_file(path),
                }
                for path in base_paths
            ],
        )

    canonical = repo / "data/canonical/puzzles.jsonl"
    if canonical.is_file():
        with canonical.open(encoding="utf-8") as handle:
            if any(
                json.loads(line).get("task_id") == task_id
                for line in handle
                if line.strip()
            ):
                return (
                    "canonical_only",
                    [
                        {
                            "path": "2/repo/data/canonical/puzzles.jsonl",
                            "repo_relpath": "data/canonical/puzzles.jsonl",
                            "sha256": sha256_file(canonical),
                        }
                    ],
                )
    raise SystemExit(
        "missing both task-local base authority and canonical task row for "
        f"{task_id}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="bundled repo directory (default: parent of this script's scripts/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="assignment path (default: REPO/../ASSIGNMENT.json)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="reproducible test seed; omit for per-copy OS randomness",
    )
    parser.add_argument("--worker-id", help="optional stable reviewer identity")
    parser.add_argument(
        "--allow-queue-mismatch",
        action="store_true",
        help=(
            "draw even when the live queue SHA differs from PACKET-MANIFEST.json "
            "(recorded LOUD in the receipt; default is to refuse)"
        ),
    )
    return parser


def packet_provenance(repo: Path) -> dict:
    """base_commit / packet digest / verified_at from the packet manifest.

    The manifest already knows the provenance the receipt used to fill with
    placeholders ("bundled-snapshot", ""), which weakened reconstruction at
    intake (v13-x WFB EWF-000518). Missing manifest is not fatal — a packet
    can legitimately be unpacked standalone — but it IS reported.
    """
    for candidate in (repo.parent / "PACKET-MANIFEST.json", repo / "PACKET-MANIFEST.json"):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception as exc:  # malformed manifest must not be silent
                print(f"LOUD: unreadable {candidate}: {exc}", file=sys.stderr)
                return {}
    print(
        "LOUD: no PACKET-MANIFEST.json beside the repo — assignment provenance "
        "falls back to bundled-snapshot placeholders",
        file=sys.stderr,
    )
    return {}


def main() -> int:
    args = build_parser().parse_args()
    repo = args.repo.resolve()
    output = (
        args.output.resolve()
        if args.output
        else (repo.parent / "ASSIGNMENT.json").resolve()
    )
    if output.exists():
        raise SystemExit(
            f"refusing to replace immutable assignment: {output}"
        )

    queue = repo / "data/derived/kimi_generator_assignment.jsonl"
    if not queue.is_file():
        raise SystemExit(f"missing bundled assignment queue: {queue}")

    # PREFLIGHT: the queue we draw from must be the queue the packet was built
    # from. A locally rebuilt queue silently produced a receipt whose SHA and
    # candidate count disagreed with the manifest (v13-x WFB EWF-000552),
    # making the assignment unverifiable at intake. Refuse by default.
    manifest = packet_provenance(repo)
    live_queue_sha = sha256_file(queue)
    manifest_queue_sha = str(manifest.get("queue_sha256") or "")
    queue_mismatch = bool(manifest_queue_sha) and manifest_queue_sha != live_queue_sha
    if queue_mismatch and not args.allow_queue_mismatch:
        raise SystemExit(
            "LOUD: queue SHA does not match PACKET-MANIFEST.json — refusing to draw.\n"
            f"  manifest queue_sha256: {manifest_queue_sha}\n"
            f"  live     queue_sha256: {live_queue_sha}\n"
            f"  queue: {queue}\n"
            "Restore the packet's queue, or re-run with --allow-queue-mismatch "
            "to record the mismatch in the receipt and continue."
        )
    if queue_mismatch:
        print(
            "LOUD: drawing from a queue that does not match PACKET-MANIFEST.json "
            f"(manifest={manifest_queue_sha} live={live_queue_sha}); recorded in receipt",
            file=sys.stderr,
        )

    candidates = load_candidates(queue, repo=repo)
    returned_repairs_path = repo / "data/derived/returned_repairs.jsonl"
    returned_task_ids = load_returned_task_ids(returned_repairs_path)
    candidates, returned_excluded, returned_fallback = avoid_returned_repairs(
        candidates,
        returned_task_ids,
    )
    if returned_fallback:
        print(
            "LOUD: every eligible pending task already has a returned repair; "
            "falling back to the pending queue instead of producing no assignment",
            file=sys.stderr,
        )
    notes_path = repo / "data/derived/generator_associated_notes.jsonl"
    notes = load_associated_notes(notes_path)
    lineage_path = repo / "data/derived/official_generator_lineage.jsonl"
    source_lineage = load_source_lineage(lineage_path)
    seed = (
        args.seed
        if args.seed is not None
        else int.from_bytes(os.urandom(16), "big")
    )
    weights = [
        1.0 + math.sqrt(max(0.0, float(row.get("priority_score") or 0.0)))
        for row in candidates
    ]
    row = random.Random(seed).choices(candidates, weights=weights, k=1)[0]
    queue_row_sha256 = canonical_digest(row)
    row = merge_assignment_preflight(
        row,
        fresh_assignment_preflight(repo, row),
    )
    generator_path = repo / str(row["path"])
    if not generator_path.is_file():
        raise SystemExit(f"missing assigned generator: {generator_path}")
    authority_mode, authority_files = task_authorities(
        repo,
        str(row["task_id"]),
        kind=str(row.get("kind") or ""),
        generator_path=generator_path,
    )

    ontology_contract = skill_ontology_contract(repo)
    token = uuid.uuid4().hex[:12]
    worker_id = args.worker_id or f"external-local-random:{token}"
    copy_id = f"local-random-{token}"
    assignment = {
        "schema_version": 1,
        "purpose": "external_generator_quality_worker",
        "batch_id": f"local-random-{token}",
        "copy_id": copy_id,
        "slot": 1,
        # Provenance comes from the packet manifest when present, so intake can
        # reconstruct exactly what was shipped (v13-x WFB EWF-000518).
        "base_commit": str(manifest.get("base_commit") or "bundled-snapshot"),
        "source_bundle": "reviews/2 packet (zip or tar.zst fallback)",
        "source_bundle_sha256": str(manifest.get("canonical_sha256") or ""),
        "packet_manifest": {
            "queue_sha256": manifest_queue_sha,
            "eligible_assignment_count": manifest.get("eligible_assignment_count"),
            "contract_version": manifest.get("contract_version"),
            "verified_at": manifest.get("verified_at"),
            "status": manifest.get("status"),
        },
        "queue_source": str(queue.relative_to(repo)),
        "queue_sha256": live_queue_sha,
        "queue_matches_packet_manifest": (not queue_mismatch) if manifest_queue_sha else None,
        "assignment_member": "ASSIGNMENT.json",
        "worker_guide": "CURRENT-GENERATOR-WORKER.md",
        "authority_path_base": "bundle_root",
        "repository_member_root": "2/repo",
        "skill_ontology_contract": ontology_contract,
        "selection_mode": "disconnected_local_random",
        "selection_strategy": "priority_weighted_random_returned_repair_avoiding",
        "collision_control": {
            "centrally_reserved": False,
            "returned_repair_ledger": str(
                returned_repairs_path.relative_to(repo)
            ),
            "returned_repair_tasks_excluded": returned_excluded,
            "returned_repair_exhaustion_fallback": returned_fallback,
            "warning": (
                "Tasks with recorded candidate returns were excluded when any "
                "fresh task remained. Independent random copies can still collide "
                "with each other; intake must deduplicate by task_id."
            ),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assignments": [
            {
                "task_id": row["task_id"],
                "worker_id": worker_id,
                "claim_expires_at": None,
                "selection_seed": seed,
                "candidate_count": len(candidates),
                "kind": row.get("kind"),
                "path": row["path"],
                "queue_rank": row.get("queue_rank"),
                "priority_score": row.get("priority_score"),
                "findings": row.get("findings") or [],
                "finding_taxonomy": row.get("finding_taxonomy") or {},
                "active_semantic_veto": bool(
                    row.get("active_semantic_veto")
                ),
                "rule_hash_expected": row.get("rule_hash_expected") or "",
                "generator_sha256": sha256_file(generator_path),
                "queue_row_sha256": queue_row_sha256,
                "assignment_checklist": row.get("assignment_checklist") or {},
                "assignment_preflight": row.get("assignment_preflight") or {},
                "associated_notes": notes.get(row["task_id"], []),
                "known_source_lineage": source_lineage.get(row["task_id"], []),
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
        ],
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
            "channel_id": copy_id,
            "worker_to_codex": {
                "markdown_member": "FEEDBACK_TO_CODEX.md",
                "results_field": "feedback_to_codex",
                "schema_member": "GENERATOR-RESULT-SCHEMA.json",
            },
            "codex_to_worker": {
                "member": "CODEX-RESPONSE.json",
                "schema_member": "CODEX-RESPONSE-SCHEMA.json",
            },
            "protocol_member": "FEEDBACK-LOOP.md",
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{token}.tmp")
    temporary.write_text(
        json.dumps(assignment, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(
        json.dumps(
            {
                "assignment": str(output),
                "copy_id": copy_id,
                "worker_id": worker_id,
                "task_id": row["task_id"],
                "candidate_count": len(candidates),
                "selection_seed": seed,
                "generator_sha256": assignment["assignments"][0][
                    "generator_sha256"
                ],
                "centrally_reserved": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
