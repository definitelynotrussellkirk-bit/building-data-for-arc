#!/usr/bin/env python3
"""Read-only final scope review for review-7b9ac74f2385b249."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "196a7ec58bbc"
ASSIGNMENT_ID = "review-7b9ac74f2385b249"
EXPECTED_GENERATOR_SHA256 = "716d964e83da3769819ffa8e4c51ed38ffd7e375643fd97a4bb574db67b69af1"
EXPECTED_RULE_HASH = "24bc23963715"
REQUIRED_REPORT_GATES = (
    "all_racket_exact",
    "all_rival_racket_python_exact",
    "all_demos_identify_setting",
    "all_queries_identifiable_from_demonstrations",
    "all_public_challenges_masked",
    "all_public_identities_visible_only",
    "public_batch_order_independent",
    "duplicate_public_payload_rejected",
    "v2_public_directory_content_addressed_only",
    "legacy_artifacts_preserved_unchanged",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def source_files(root: Path) -> set[Path]:
    return {
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.relative_to(root).parts)
        and path.suffix not in {".pyc", ".pyo"}
    }


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("final_review_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    if repo.name != "repo":
        raise SystemExit(f"run from WORK/repo, got {repo}")
    work = repo.parent
    task = repo / "generators" / TASK_ID
    baseline_task = work / ".review" / "baseline" / "repo" / "generators" / TASK_ID
    checks = work / "checks"
    failures: list[str] = []

    assignment = load_json(work / "ASSIGNMENT.json")
    if assignment.get("assignment_id") != ASSIGNMENT_ID:
        failures.append("assignment id mismatch")

    report_path = checks / "parametric" / "196a7ec58bbc-handedness-v2.json"
    report = load_json(report_path)
    public_ids = sorted(row["public_id"] for row in report.get("settings", []))

    expected_modified = {
        Path("notes.md"),
        Path("tests/test_generator_196a7ec58bbc.py"),
        Path("workspace/parametric/README.md"),
        Path("workspace/parametric/evidence/manifest.json"),
        Path("workspace/parametric/prototype.py"),
        Path("workspace/parametric/verify.py"),
    }
    expected_new = {
        Path("workspace/parametric/episodes/private/clockwise-complete.json"),
        Path("workspace/parametric/episodes/private/counterclockwise-complete.json"),
        *(Path(f"workspace/parametric/episodes/public/challenge-{identifier}.json") for identifier in public_ids),
    }

    base_files = source_files(baseline_task)
    current_files = source_files(task)
    deleted = sorted(str(path) for path in base_files - current_files)
    new = sorted(str(path) for path in current_files - base_files)
    modified = sorted(
        str(path)
        for path in base_files & current_files
        if (baseline_task / path).read_bytes() != (task / path).read_bytes()
    )
    if deleted:
        failures.append(f"baseline files deleted: {deleted}")
    if set(map(Path, modified)) != expected_modified:
        failures.append(f"unexpected modified paths: {modified}")
    if set(map(Path, new)) != expected_new:
        failures.append(f"unexpected new paths: {new}")

    generator_path = task / "generator.py"
    generator_sha = sha256(generator_path)
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        failures.append(f"production generator changed: {generator_sha}")
    generator = load_generator(generator_path)
    if getattr(generator, "RULE_HASH", None) != EXPECTED_RULE_HASH:
        failures.append(f"canonical RULE_HASH changed: {getattr(generator, 'RULE_HASH', None)!r}")

    canonical_rel = "repo/shared/data/canonical/puzzles.jsonl"
    canonical_path = work / canonical_rel
    expected_canonical_sha = assignment["baseline_sha256"][canonical_rel]
    canonical_sha = sha256(canonical_path)
    if canonical_sha != expected_canonical_sha:
        failures.append("canonical puzzles file differs from packet baseline")

    gate_values = {key: report.get(key) for key in REQUIRED_REPORT_GATES}
    for key, value in gate_values.items():
        if value is not True:
            failures.append(f"report gate {key} is {value!r}")
    if report.get("schema") != "196a7ec58bbc-parametric-handedness-v2":
        failures.append("unexpected v2 report schema")
    if report.get("status") != "proposed_prototype_not_selected":
        failures.append("prototype status is not explicitly unselected")
    if report.get("retained_counts") != {"demonstrations": 3, "queries": 4}:
        failures.append("retained counts are not exactly 3 demonstrations / 4 queries")
    if report.get("unique_input_count") != 14:
        failures.append("retained episodes do not have 14 globally unique inputs")
    if len(report.get("settings", [])) != 2:
        failures.append("expected exactly two retained settings")

    for row in report.get("settings", []):
        setting = row.get("setting")
        if (row.get("demonstration_count"), row.get("query_count")) != (3, 4):
            failures.append(f"{setting}: wrong pair counts")
        if row.get("unique_episode_input_count") != 7:
            failures.append(f"{setting}: inputs are not all distinct")
        if not row.get("all_racket_exact") or not row.get("rival_racket_python_exact"):
            failures.append(f"{setting}: Racket parity failed")
        queries = row.get("queries", [])
        if len(queries) != 4 or not all(item.get("identifiable_from_demonstrations") for item in queries):
            failures.append(f"{setting}: four-query identifiability failed")

    source_hashes = report.get("source_hashes", {})
    for relative, expected in source_hashes.items():
        actual = sha256(repo / relative)
        if actual != expected:
            failures.append(f"source hash mismatch for {relative}: {actual}")

    public_dir = task / "workspace" / "parametric" / "episodes" / "public"
    actual_public_names = sorted(path.name for path in public_dir.glob("*.json"))
    expected_public_names = sorted(f"challenge-{identifier}.json" for identifier in public_ids)
    if actual_public_names != expected_public_names:
        failures.append(f"v2 public directory mismatch: {actual_public_names}")
    for identifier in public_ids:
        path = public_dir / f"challenge-{identifier}.json"
        if sha256(path) != identifier:
            failures.append(f"public bytes do not hash to filename: {path.name}")
        payload = load_json(path)
        if set(payload) != {"train", "test"}:
            failures.append(f"public payload has private top-level fields: {path.name}")
        if any(set(pair) != {"input", "output"} for pair in payload.get("train", [])):
            failures.append(f"public demonstrations malformed: {path.name}")
        if any(set(pair) != {"input"} for pair in payload.get("test", [])):
            failures.append(f"public queries reveal answers: {path.name}")

    for name, row in report.get("legacy_artifacts", {}).items():
        path = task / "workspace" / "parametric" / "episodes" / name
        if sha256(path) != row.get("expected_sha256"):
            failures.append(f"legacy evidence changed: {name}")

    readme = (task / "workspace" / "parametric" / "README.md").read_text()
    for required in ("--demonstrations 3 --queries 4", "--public-dir", "byte-for-byte as archival evidence", "not members of the corrected v2 public export"):
        if required not in readme:
            failures.append(f"README missing: {required}")
    notes = (task / "notes.md").read_text()
    for required in (ASSIGNMENT_ID, "default `3/1`; retained evidence `3/4`", "hash-pinned and excluded from the corrected v2"):
        if required not in notes:
            failures.append(f"notes missing: {required}")

    results = load_json(work / "RESULTS.json")
    ticket_rows = results.get("supplementary_tickets", [])
    expected_tickets = {"ticket-5ade2f847a3f6eb8", "ticket-f9837c8ad37973df"}
    if {row.get("ticket_id") for row in ticket_rows} != expected_tickets or len(ticket_rows) != 2:
        failures.append("RESULTS.json does not contain exactly the two assigned tickets")
    if any(row.get("status") != "completed" for row in ticket_rows):
        failures.append("one or more ticket rows is not completed")

    first_ticket = load_json(checks / "tickets" / "ticket-5ade2f847a3f6eb8" / "result.json")
    if not (
        first_ticket.get("source_bound") is True
        and first_ticket.get("status") == "reproduced"
        and first_ticket.get("lesson", {}).get("fresh_racket_matches_retained") is True
        and first_ticket.get("lesson", {}).get("fits_all_four_demonstrations") is True
        and first_ticket.get("lesson", {}).get("fails_query") is True
    ):
        failures.append("audit replay ticket result is incomplete")
    second_ticket = load_json(checks / "tickets" / "ticket-f9837c8ad37973df" / "result.json")
    if not (
        second_ticket.get("source_bound") is True
        and second_ticket.get("status") == "limitation_reproduced"
        and second_ticket.get("count_boundary", {}).get("supports_four_simultaneous_queries") is False
        and second_ticket.get("privacy_boundary", {}).get("filenames_content_derived") is False
        and second_ticket.get("approval", {}).get("variant_approved") is False
    ):
        failures.append("parameter-query ticket result is incomplete")

    report_out = {
        "schema": "arcpuzzles-author-self-review-v2",
        "assignment_id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "independence": "author self-review; no independent subagent/reviewer tool available",
        "changed_paths": {"modified": modified, "new": new, "deleted": deleted},
        "authority": {
            "generator_sha256": generator_sha,
            "generator_unchanged": generator_sha == EXPECTED_GENERATOR_SHA256,
            "rule_hash": getattr(generator, "RULE_HASH", None),
            "canonical_file_sha256": canonical_sha,
            "canonical_file_unchanged": canonical_sha == expected_canonical_sha,
        },
        "prototype_report": {
            "path": str(report_path.relative_to(work)),
            "gates": gate_values,
            "retained_counts": report.get("retained_counts"),
            "setting_count": len(report.get("settings", [])),
            "unique_input_count": report.get("unique_input_count"),
            "public_files": actual_public_names,
        },
        "tickets": {
            "audit_replay_status": first_ticket.get("status"),
            "parameter_queries_status": second_ticket.get("status"),
            "result_rows": len(ticket_rows),
        },
        "review_findings": {"critical": [], "important": [], "minor": []},
        "bounded_claims": [
            "Only two retained episodes, one per handedness setting, were Racket-verified.",
            "Identifiability is checked against the declared opposite-handedness rival, not every possible program.",
            "This is an author self-review rather than an independent review.",
        ],
        "failures": failures,
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report_out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report_out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
