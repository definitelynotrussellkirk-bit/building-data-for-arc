#!/usr/bin/env python3
"""Recheck the selected-task delta, retained evidence, and ticket handoff."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT = Path(__file__).resolve()
WORK = SCRIPT.parents[2]
REPO = WORK / "repo"
BASELINE = WORK / ".review" / "baseline" / "repo"
TASK = "3f26d45b9f51"
TASK_HOME = REPO / "generators" / TASK
EVIDENCE = WORK / "checks" / "parametric" / "connection-axes-v1"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    current_generator = TASK_HOME / "generator.py"
    baseline_generator = BASELINE / "generators" / TASK / "generator.py"
    current_canonical = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    baseline_canonical = BASELINE / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if current_generator.read_bytes() != baseline_generator.read_bytes():
        raise AssertionError("production generator differs from packet baseline")
    if current_canonical.read_bytes() != baseline_canonical.read_bytes():
        raise AssertionError("canonical ledger differs from packet baseline")

    report = load(EVIDENCE / "report.json")
    manifest = load(EVIDENCE / "manifest.json")
    if report["status"] != "passed_bounded_prototype_evidence":
        raise AssertionError("prototype report is not passing")
    if report["prototype_status"] != "proposed_unapproved":
        raise AssertionError("prototype status lost its unapproved boundary")
    source_paths = {
        "generator_sha256": REPO / report["source"]["generator_path"],
        "prototype_sha256": REPO / report["source"]["prototype_path"],
        "test_sha256": REPO / report["source"]["test_path"],
        "verifier_sha256": REPO / report["source"]["verifier_path"],
    }
    for key, path in source_paths.items():
        if report["source"][key] != sha256(path):
            raise AssertionError(f"report source hash mismatch: {key}")

    actual_files = {
        path.relative_to(EVIDENCE).as_posix()
        for path in EVIDENCE.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if set(manifest["files"]) != actual_files:
        raise AssertionError("manifest file set differs from evidence directory")
    for relative, metadata in manifest["files"].items():
        path = EVIDENCE / relative
        if metadata != {"bytes": path.stat().st_size, "sha256": sha256(path)}:
            raise AssertionError(f"manifest metadata mismatch: {relative}")

    episodes = report["episodes"]
    identifiers = [row["public_identifier"] for row in episodes]
    if identifiers != sorted(identifiers) or len(set(identifiers)) != 3:
        raise AssertionError("public challenge identifiers are not unique and sorted")
    if len({row["difficulty"] for row in episodes}) != 1:
        raise AssertionError("setting comparison episodes do not share one difficulty")
    if {row["setting"] for row in episodes} != {"both", "horizontal", "vertical"}:
        raise AssertionError("evidence does not cover exactly the three settings")
    for row in episodes:
        private = load(EVIDENCE / "private" / f"episode-{row['setting']}.json")
        if len(private["train"]) != 3 or len(private["test"]) != 4:
            raise AssertionError("episode counts changed")
        public_path = EVIDENCE / "public" / row["public_identifier"]
        if public_path.read_bytes() != public_challenge_bytes(private):
            raise AssertionError(f"public/private projection mismatch: {public_path.name}")

    audit = load(WORK / "checks" / "parametric" / "adversarial" / "audit-report.json")
    if audit["status"] != "passed" or audit["parity"]["status"] != "passed" or audit["privacy"]["status"] != "passed":
        raise AssertionError("independent parametric audit is not passing")

    ticket1 = load(WORK / "checks" / "tickets" / "ticket-e4c31fb83b169f83" / "receipt.json")
    ticket2 = load(WORK / "checks" / "tickets" / "ticket-2c0d4ab8880990b2" / "receipt.json")
    if ticket1["status"] != "completed" or ticket1["bounded_claim_reproduced"] is not True:
        raise AssertionError("audit replay ticket is incomplete")
    if ticket2["status"] != "finding" or ticket2["retained_witness_reproduced_byte_exact"] is not True:
        raise AssertionError("adversarial witness ticket is incomplete")

    results = load(WORK / "RESULTS.json")
    if results["completion_state"] != "complete":
        raise AssertionError("RESULTS.json is not marked complete")
    tickets = results.get("supplementary_tickets")
    if not isinstance(tickets, list) or len(tickets) != 2:
        raise AssertionError("RESULTS.json must contain exactly two ticket rows")
    for row in tickets:
        for relative in row["evidence_paths"]:
            if not (WORK / relative).is_file():
                raise AssertionError(f"missing ticket evidence path: {relative}")
    for command in results.get("verification_commands", []):
        for relative in command.get("evidence_paths", []):
            if not (WORK / relative).is_file():
                raise AssertionError(f"missing command evidence path: {relative}")
    for name in ("REVIEW.md", "AUDIT.md", "FEEDBACK_TO_CODEX.md"):
        if not (WORK / name).is_file():
            raise AssertionError(f"missing required document: {name}")

    output = {
        "schema": "3f26d45b9f51-final-integrity-v1",
        "status": "passed",
        "production_generator": {"unchanged": True, "sha256": sha256(current_generator)},
        "canonical_ledger": {"unchanged": True, "sha256": sha256(current_canonical)},
        "prototype": {
            "status": report["prototype_status"],
            "settings": len(episodes),
            "difficulty": episodes[0]["difficulty"],
            "demos_per_episode": report["counts"]["demos_per_episode"],
            "queries_per_episode": report["counts"]["queries_per_episode"],
            "manifest_files": len(manifest["files"]),
        },
        "tickets": [
            {"ticket_id": ticket1["ticket_id"], "status": ticket1["status"]},
            {"ticket_id": ticket2["ticket_id"], "status": ticket2["status"]},
        ],
    }
    out = WORK / "checks" / "parametric" / "command-records" / "final-integrity.json"
    out.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
