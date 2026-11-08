#!/usr/bin/env python3
"""Validate the package-ready review handoff without rerunning live probes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


WORK = Path(__file__).resolve().parents[1]
REPO = WORK / "repo"
TASK_ID = "4c26a1072222"
ASSIGNMENT_ID = "review-d262182682b4f569"
GENERATOR_SHA256 = "5816599d9ed224a6d95f56745292449c464b6e708cac9373db58e8671b8aa22d"
RULE_HASH = "a86a18b84011"
TICKET_IDS = {
    "ticket-67dc84a75e188d06",
    "ticket-39b2589aa4b0c084",
}
TICKET_KEYS = {
    "ticket_id",
    "type",
    "status",
    "summary",
    "evidence_paths",
    "elapsed_minutes",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    results = json.loads((WORK / "RESULTS.json").read_text(encoding="utf-8"))
    assert results["completion_state"] == "complete"
    assert results["assignment_id"] == ASSIGNMENT_ID
    assert results["task_id"] == TASK_ID
    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    assert results["generator_sha256"] == sha256(generator_path) == GENERATOR_SHA256
    assert results["rule_hash"] == RULE_HASH
    assert not (WORK / "AUDIT.md").exists()

    tickets = results["supplementary_tickets"]
    assert len(tickets) == 2
    assert {row["ticket_id"] for row in tickets} == TICKET_IDS
    for row in tickets:
        assert set(row) == TICKET_KEYS
        assert row["status"] == "completed"
        for relative in row["evidence_paths"]:
            assert (WORK / relative).is_file(), relative

    for record in results["verification_commands"]:
        assert record["exit_status"] == 0
        assert record["status"] == "passed"
        for relative in record["evidence_paths"]:
            assert (WORK / relative).exists(), relative

    manifest_path = WORK / "checks" / "parametric" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "passed"
    assert manifest["counts"] == {
        "episodes": 2,
        "query_pairs_per_episode": 4,
        "racket_executions": 32,
        "settings_available": 2,
        "train_pairs_per_episode": 4,
    }
    ids = [row["public_id"] for row in manifest["episodes"]]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids)) == 2
    for row in manifest["episodes"]:
        public_id = row["public_id"]
        episode_dir = manifest_path.parent / public_id
        public_path = episode_dir / "public.json"
        public_bytes = public_path.read_bytes()
        assert hashlib.sha256(public_bytes).hexdigest() == public_id
        assert row["files"]["public.json"]["sha256"] == public_id
        public = json.loads(public_bytes)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert (episode_dir / "private.json").is_file()
        assert (episode_dir / "rule.rkt").is_file()

    parametric_dir = REPO / "generators" / TASK_ID / "workspace" / "parametric"
    for name, expected in manifest["prototype_source_sha256"].items():
        assert sha256(parametric_dir / name) == expected, name
    assert manifest["generator_sha256"] == GENERATOR_SHA256

    task_dir = REPO / "generators" / TASK_ID
    assert not list(task_dir.rglob("__pycache__"))
    assert not list(task_dir.rglob("*.pyc"))
    executable_sources = [
        path.relative_to(WORK).as_posix()
        for path in task_dir.rglob("*")
        if path.is_file() and path.stat().st_mode & 0o111
    ]
    assert not executable_sources, executable_sources

    checks_dir = WORK / "checks"
    assert not list(checks_dir.rglob("__pycache__"))
    assert not list(checks_dir.rglob("*.pyc"))
    assert not list(checks_dir.rglob("*.pyo"))

    print(
        json.dumps(
            {
                "status": "passed",
                "focused_test_count": 32,
                "racket_executions": manifest["counts"]["racket_executions"],
                "public_ids": ids,
                "supplementary_tickets": sorted(TICKET_IDS),
                "generator_sha256": GENERATOR_SHA256,
                "rule_hash": RULE_HASH,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
