#!/usr/bin/env python3
"""Verify that a review packet can serve every bundled random assignment."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


REQUIRED_BUNDLE_PATHS = (
    "README.md",
    "CURRENT-GENERATOR-WORKER.md",
    "FEEDBACK-LOOP.md",
    "GENERATOR-RESULT-SCHEMA.json",
    "PACKET-CONFIG.json",
    "STRATEGY-REVIEW-CADENCE.json",
    "repo/AGENTS.md",
    "repo/CLAUDE.md",
    "repo/GUIDE",
    "repo/KIMIgeneratorASSIGNMENT.md",
    "repo/README.md",
    "repo/QWEN3.8-27b/README.md",
    "repo/QWEN3.8-27b/MODEL_SOURCES.json",
    "repo/QWEN3.8-27b/STRATEGY.md",
    "repo/requirements.txt",
    "repo/reviews/path_bootstrap.py",
    "repo/arc_repl/racket_bridge.py",
    "repo/arc_repl/racket_prelude",
    "repo/data/base/solutions",
    "repo/data/canonical/puzzle_db.jsonl",
    "repo/data/canonical/puzzles.jsonl",
    "repo/data/derived/generator_associated_notes.jsonl",
    "repo/data/derived/official_generator_lineage.jsonl",
    "repo/data/derived/official_generator_coverage.json",
    "repo/data/derived/official_generator_backlog.jsonl",
    "repo/data/derived/official_skill_coverage.json",
    "repo/data/derived/official_skill_coverage.md",
    "repo/data/derived/kimi_generator_assignment.jsonl",
    "repo/docs",
    "repo/puzzle_generators/generic",
    "repo/puzzle_generators/per_puzzle",
    "repo/scripts/bootstrap_random_generator_assignment.py",
    "repo/scripts/audit_official_generator_lineage.py",
    "repo/scripts/build_question_only_review_packet.py",
    "repo/scripts/check_generator_override_contract.py",
    "repo/scripts/generator_defect_lint.py",
    "repo/scripts/generator_distribution_gate.py",
    "repo/scripts/generator_selfcheck.py",
    "repo/scripts/generic_generator_parity.py",
    "repo/scripts/racket_linter.py",
    "repo/scripts/rule_smoke.py",
    "repo/solvers/grounded_rules.py",
    "repo/src",
    "repo/tests",
    "repo/vendor/racket-minimal-8.17-x86_64-linux-cs.tgz",
)

WORKER_CONTRACT_RE = re.compile(r"^CONTRACT_VERSION:\s*(\d+)\b", re.MULTILINE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            yield row


def eligible_rows(queue: Path) -> list[dict[str, Any]]:
    return [
        row
        for row in jsonl_rows(queue)
        if row.get("status") == "pending"
        and row.get("train_safety") != "reviewed_safe"
    ]


def canonical_task_ids(path: Path) -> set[str]:
    return {
        str(row["task_id"])
        for row in jsonl_rows(path)
        if isinstance(row.get("task_id"), str) and row["task_id"]
    }


def base_authority_index(root: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for path in sorted(root.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        task_id = row.get("task_id") if isinstance(row, dict) else None
        if isinstance(task_id, str) and task_id:
            result[task_id].append(path.relative_to(root).as_posix())
    return dict(result)


def payload_files(bundle: Path) -> list[Path]:
    excluded = {"PACKET-FILES.sha256"}
    return [
        path
        for path in sorted(bundle.rglob("*"))
        if path.is_file()
        and path.name not in excluded
        and "__pycache__" not in path.parts
        and ".git" not in path.parts
    ]


def validate_strategy_cadence(bundle: Path) -> tuple[list[str], int | None]:
    errors: list[str] = []
    path = bundle / "STRATEGY-REVIEW-CADENCE.json"
    try:
        cadence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid strategy review cadence: {exc}"], None
    target_mix = cadence.get("target_mix")
    buckets = cadence.get("round_buckets")
    try:
        round_size = int(cadence.get("round_size"))
        counts = {str(key): int(value) for key, value in target_mix.items()}
    except (AttributeError, TypeError, ValueError):
        return ["strategy cadence round_size/target_mix is malformed"], None
    if round_size < 1 or sum(counts.values()) != round_size:
        errors.append("strategy cadence target_mix does not sum to round_size")
    if not isinstance(buckets, dict):
        errors.append("strategy cadence round_buckets is missing")
        return errors, round_size

    bank: dict[str, dict[str, Any]] = {}
    for question_path in sorted((bundle / "questions/bank").glob("QT-*.json")):
        try:
            row = json.loads(question_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid question bank row {question_path.name}: {exc}")
            continue
        if isinstance(row, dict) and isinstance(row.get("question_id"), str):
            bank[row["question_id"]] = row
    eligible = {
        qid for qid, row in bank.items() if row.get("status") in {"open", "active"}
    }
    if len(eligible) < round_size:
        errors.append("question bank has too few eligible rows for one strategy round")
    reserved: set[str] = set()
    for bucket, count in counts.items():
        if count < 0:
            errors.append(f"strategy cadence bucket {bucket!r} has negative count")
            continue
        if bucket == "unrestricted_random":
            continue
        identifiers = buckets.get(bucket)
        if not isinstance(identifiers, list):
            errors.append(f"strategy cadence lacks bucket list {bucket!r}")
            continue
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"strategy cadence bucket {bucket!r} contains duplicates")
        available = {qid for qid in identifiers if qid in eligible}
        if len(available) < count:
            errors.append(
                f"strategy cadence bucket {bucket!r} has {len(available)} "
                f"eligible questions for {count} slots"
            )
        overlap = reserved & available
        if overlap:
            errors.append(
                f"strategy cadence buckets overlap: {', '.join(sorted(overlap))}"
            )
        reserved.update(available)

    active_round = cadence.get("active_round")
    if active_round is not None:
        if (
            not isinstance(active_round, str)
            or not active_round
            or Path(active_round).is_absolute()
            or ".." in Path(active_round).parts
        ):
            errors.append("strategy cadence active_round path is unsafe")
        else:
            active_path = bundle / active_round
            try:
                active = json.loads(active_path.read_text(encoding="utf-8"))
                questions = active["questions"]
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                errors.append(f"invalid active strategy round: {exc}")
            else:
                identifiers = [row.get("question_id") for row in questions]
                observed_mix = Counter(row.get("round_bucket") for row in questions)
                if len(questions) != round_size:
                    errors.append("active strategy round has wrong number of questions")
                if len(set(identifiers)) != len(identifiers):
                    errors.append("active strategy round contains duplicate questions")
                if observed_mix != Counter(counts):
                    errors.append("active strategy round does not match target_mix")
                unknown = sorted(set(identifiers) - set(bank))
                if unknown:
                    errors.append(
                        "active strategy round references unknown questions: "
                        + ", ".join(unknown)
                    )
    return errors, round_size


def validate_contract_version(bundle: Path) -> tuple[list[str], int | None]:
    errors: list[str] = []
    try:
        config = json.loads((bundle / "PACKET-CONFIG.json").read_text(encoding="utf-8"))
        configured = config["contract_version"]
        if isinstance(configured, bool):
            raise TypeError("boolean is not a contract version")
        configured = int(configured)
        if configured < 1:
            raise ValueError("contract version must be positive")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return [f"invalid packet contract version authority: {exc}"], None

    try:
        guide = (bundle / "CURRENT-GENERATOR-WORKER.md").read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read worker guide contract version: {exc}"], configured
    match = WORKER_CONTRACT_RE.search(guide)
    if match is None:
        errors.append("worker guide lacks a CONTRACT_VERSION header")
    elif int(match.group(1)) != configured:
        errors.append(
            "worker guide contract version "
            f"{match.group(1)} disagrees with PACKET-CONFIG.json {configured}"
        )
    return errors, configured


def verify_bundle(bundle: Path) -> tuple[dict[str, Any], list[str]]:
    bundle = bundle.resolve()
    repo = bundle / "repo"
    errors = [
        f"missing required packet path: {relative}"
        for relative in REQUIRED_BUNDLE_PATHS
        if not (bundle / relative).exists()
    ]
    contract_errors, contract_version = validate_contract_version(bundle)
    errors.extend(contract_errors)
    cadence_errors, strategy_round_size = validate_strategy_cadence(bundle)
    errors.extend(cadence_errors)

    queue = repo / "data/derived/kimi_generator_assignment.jsonl"
    canonical = repo / "data/canonical/puzzles.jsonl"
    base_root = repo / "data/base/solutions"
    if not queue.is_file() or not canonical.is_file() or not base_root.is_dir():
        return {}, errors or ["packet is missing queue/canonical/base data"]

    candidates = eligible_rows(queue)
    canonical_ids = canonical_task_ids(canonical)
    base_index = base_authority_index(base_root)
    authority_modes: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    missing_generators: list[str] = []
    missing_authorities: list[str] = []
    missing_declared_authorities: list[str] = []

    for row in candidates:
        task_id = str(row.get("task_id") or "")
        kind = str(row.get("kind") or "unknown")
        kinds[kind] += 1
        generator_rel = row.get("path")
        if (
            not isinstance(generator_rel, str)
            or not generator_rel
            or not (repo / generator_rel).is_file()
        ):
            missing_generators.append(task_id or repr(generator_rel))

        declared = row.get("rule_authority")
        if (
            isinstance(declared, str)
            and declared
            and not (repo / declared).is_file()
        ):
            missing_declared_authorities.append(f"{task_id}:{declared}")

        if base_index.get(task_id):
            authority_modes["task_local_base"] += 1
        elif kind == "generic":
            authority_modes["generic_embedded_program"] += 1
        elif task_id in canonical_ids:
            authority_modes["canonical_only"] += 1
        else:
            missing_authorities.append(task_id)

    if missing_generators:
        errors.append(
            f"{len(missing_generators)} eligible task(s) lack generators: "
            + ", ".join(missing_generators[:12])
        )
    if missing_declared_authorities:
        errors.append(
            f"{len(missing_declared_authorities)} declared authority path(s) "
            "are missing: "
            + ", ".join(missing_declared_authorities[:12])
        )
    if missing_authorities:
        errors.append(
            f"{len(missing_authorities)} per-puzzle task(s) have neither a "
            "task-local base authority nor a canonical row: "
            + ", ".join(missing_authorities[:12])
        )

    files = payload_files(bundle)
    manifest = {
        "schema_version": 1,
        "contract_version": contract_version,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verification_scope": (
            "all pending non-reviewed-safe assignments in the bundled queue"
        ),
        "eligible_assignment_count": len(candidates),
        "assignment_kinds": dict(sorted(kinds.items())),
        "authority_coverage": dict(sorted(authority_modes.items())),
        "base_authority_task_count": len(base_index),
        "canonical_task_count": len(canonical_ids),
        "required_paths_checked": len(REQUIRED_BUNDLE_PATHS),
        "strategy_review_round_size": strategy_round_size,
        "payload_file_count_excluding_hash_list": len(files),
        "payload_bytes_excluding_hash_list": sum(
            path.stat().st_size for path in files
        ),
        "queue_sha256": sha256_file(queue),
        "canonical_sha256": sha256_file(canonical),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    return manifest, errors


def write_hashes(bundle: Path, output: Path) -> int:
    files = payload_files(bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for path in files:
            relative = path.relative_to(bundle).as_posix()
            handle.write(f"{sha256_file(path)}  {relative}\n")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle",
        nargs="?",
        type=Path,
        default=Path("reviews/2"),
    )
    parser.add_argument("--write-manifest", type=Path)
    parser.add_argument("--write-sha256", type=Path)
    args = parser.parse_args()

    manifest, errors = verify_bundle(args.bundle)
    if args.write_manifest:
        args.write_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.write_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.write_sha256:
        count = write_hashes(args.bundle.resolve(), args.write_sha256.resolve())
        print(f"wrote {count} payload hashes to {args.write_sha256}")
    print(
        "generator-review packet PASS: "
        f"{manifest['eligible_assignment_count']} eligible assignments, "
        f"{manifest['payload_file_count_excluding_hash_list']} files, "
        f"{manifest['payload_bytes_excluding_hash_list']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
