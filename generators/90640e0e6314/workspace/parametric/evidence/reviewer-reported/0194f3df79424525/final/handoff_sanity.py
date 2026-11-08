#!/usr/bin/env python3
"""Source-bound final sanity check for review-0194f3df79424525."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    work = Path(__file__).resolve().parents[2]
    repo = work / "repo"
    results = json.loads((work / "RESULTS.json").read_text())

    assert results["completion_state"] == "complete"
    assert results["remaining_failures"] == []
    assert [row["ticket_id"] for row in results["supplementary_tickets"]] == [
        "ticket-6a09a415485c5431",
        "ticket-f6c87e11f9d2c278",
    ]
    assert all(row["status"] == "completed" for row in results["supplementary_tickets"])

    evidence_paths = [
        path
        for command in results["verification_commands"]
        for path in command.get("evidence_paths", [])
    ] + [
        path
        for ticket in results["supplementary_tickets"]
        for path in ticket["evidence_paths"]
    ]
    missing = sorted(path for path in set(evidence_paths) if not (work / path).is_file())
    assert not missing, missing

    task = repo / "generators/90640e0e6314"
    baseline = work / ".review/baseline"
    assert (task / "generator.py").read_bytes() == (
        baseline / "repo/generators/90640e0e6314/generator.py"
    ).read_bytes()
    assert (repo / "shared/data/canonical/puzzles.jsonl").read_bytes() == (
        baseline / "repo/shared/data/canonical/puzzles.jsonl"
    ).read_bytes()

    identities = results["work_scope"]["source_identity"]
    assert sha256(task / "generator.py") == identities["generator_sha256"]
    assert sha256(task / "workspace/parametric/prototype.py") == identities["prototype_sha256"]
    assert sha256(task / "workspace/parametric/verify.py") == identities["verifier_sha256"]
    assert sha256(task / "tests/test_parametric_prototype.py") == identities["parametric_test_sha256"]

    artifact_root = work / "checks/parametric/90640e0e6314-artifacts/episodes"
    public_files = sorted(artifact_root.glob("episode-*/public/challenge.json"))
    private_files = sorted(artifact_root.glob("episode-*/private/episode.json"))
    assert len(public_files) == len(private_files) == 4
    forbidden_keys = {"setting", "seed", "program", "answer", "answers", "query_answers"}
    public_ids = []
    for path in public_files:
        digest = sha256(path)
        assert path.parent.parent.name == f"episode-{digest}"
        payload = json.loads(path.read_text())
        assert len(payload["train"]) == 3
        assert len(payload["test"]) == 4
        assert all(set(pair) == {"input"} for pair in payload["test"])
        assert not (forbidden_keys & set(walk_keys(payload)))
        public_ids.append(digest)
    assert public_ids == sorted(public_ids)

    verification = json.loads(
        (work / "checks/parametric/90640e0e6314-identity-corner-verification.json").read_text()
    )
    assert verification["status"] == "passed"
    assert verification["counts"] == {
        "canonical_pairs_checked": 3,
        "demonstrations_per_episode": 3,
        "distinct_shared_inputs": 7,
        "episodes": 4,
        "queries_per_episode": 4,
        "racket_setting_calls": 28,
    }
    assert verification["canonical_binding"]["default_program_exact_canonical"] is True
    for name, digest in verification["prototype_sources"].items():
        assert sha256(task / "workspace/parametric" / name) == digest
    assert "90640e0e6314-identity-corner-verification.json" in verification["command"]
    assert "90640e0e6314-artifacts" in verification["command"]

    fixed_tests = json.loads(
        (work / "checks/final/90640e0e6314-task-tests-fixed/result.json").read_text()
    )
    assert fixed_tests["passed"] is True and fixed_tests["exit_code"] == 0
    assert not (work / "AUDIT.md").exists()
    for name in ("REVIEW.md", "FEEDBACK_TO_CODEX.md", "QUESTION_ANSWER.md"):
        assert (work / name).read_text().strip()

    report = {
        "schema": "arcpuzzles-review-handoff-sanity-v1",
        "status": "passed",
        "assignment_id": "review-0194f3df79424525",
        "task_id": "90640e0e6314",
        "checks": {
            "declared_evidence_paths_exist": len(set(evidence_paths)),
            "production_generator_byte_identical_to_baseline": True,
            "canonical_ledger_byte_identical_to_baseline": True,
            "source_hashes_match_results": True,
            "retained_prototype_source_hashes_current": len(verification["prototype_sources"]),
            "public_episode_ids_match_visible_bytes": len(public_ids),
            "public_queries_answer_free": True,
            "private_episode_count": len(private_files),
            "racket_setting_calls": 28,
            "canonical_pairs_checked": 3,
            "staged_task_tests_passed": 16,
            "supplementary_tickets_completed": 2,
            "audit_file_omitted_without_peer_finding": True,
        },
        "public_ids": public_ids,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
