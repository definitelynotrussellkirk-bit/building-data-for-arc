#!/usr/bin/env python3
"""Replay the final task-local return invariants from the packet workspace."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


repo = Path.cwd().resolve()
work = repo.parent
task = repo / "generators/0ed4fa8c0b40"
assignment = json.loads((work / "ASSIGNMENT.json").read_text())
manifest_path = task / "workspace/parametric/evidence/manifest.json"
manifest = json.loads(manifest_path.read_text())

checks: dict[str, object] = {}
expected_generator = assignment["generator"]["generator_sha256"]
checks["canonical_generator_sha256"] = sha256(task / "generator.py")
assert checks["canonical_generator_sha256"] == expected_generator
assert manifest["canonical_rule_hash"] == assignment["generator"]["rule_hash"]

historical_names = [
    "mirror-gap0_public.json",
    "mirror-gap1_public.json",
    "translate-gap0_public.json",
    "translate-gap1_public.json",
]
examples = task / "workspace/parametric/examples"
historical = {}
for name in historical_names:
    path = examples / name
    relative = path.relative_to(work).as_posix()
    digest = sha256(path)
    assert digest == assignment["baseline_sha256"][relative]
    historical[name] = digest
checks["historical_examples_unchanged"] = historical

current_dir = examples / "current"
current = []
for path in sorted(current_dir.glob("*.json")):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    assert path.stem == digest
    assert len(value["train"]) == 3
    assert len(value["test"]) == 4
    assert all(set(pair) == {"input"} for pair in value["test"])
    current.append({"path": path.relative_to(repo).as_posix(), "sha256": digest})
assert len(current) == 4
checks["current_public_examples"] = current

inventory = []
for row in manifest["files"]:
    path = repo / row["path"]
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_size == row["bytes"]
    assert sha256(path) == row["sha256"]
    inventory.append(row["path"])
checks["manifest_sha256"] = sha256(manifest_path)
checks["manifest_inventory_count"] = len(inventory)
checks["manifest_status"] = manifest["public_identifier_status"]

focused = (work / "checks/parametric/focused-tests.log").read_text()
assert "79 passed" in focused
checks["focused_tests"] = "79 passed"

results = json.loads((work / "RESULTS.json").read_text())
for command in results["verification_commands"]:
    for relative in command.get("evidence_paths", []):
        path = work / relative
        assert path.is_file(), relative
checks["verification_evidence_paths_exist"] = True
checks["supplementary_ticket_count"] = len(results["supplementary_tickets"])
assert checks["supplementary_ticket_count"] == 2

report = {
    "schema": "arcpuzzles-final-consistency-v1",
    "assignment_id": assignment["assignment_id"],
    "task_id": assignment["task_id"],
    "status": "pass",
    "checks": checks,
}
out = work / "checks/final-consistency.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "pass", "out": str(out), "checks": len(checks)}, sort_keys=True))
