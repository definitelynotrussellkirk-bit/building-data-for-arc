#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[2]
REPO = WORK / "repo"
BASE = WORK / ".review" / "baseline" / "repo"
for path in (REPO / "src", REPO / "shared" / "runtime"):
    sys.path.insert(0, str(path))

from arcpuzzles import Catalog
from arcpuzzles.parametric_priority import _prototype

TASK = "506e262f9354"
EXPECTED_GENERATOR = "762a30ac71d7bb9e779a6ce0948247878740259cac499842ef991e2863f20ec5"
EXPECTED_RULE = "d19e95f77d58"
EXPECTED_CANONICAL_PROGRAM = "7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f"
EXPECTED_CHANGED = [
    "generators/506e262f9354/notes.md",
    "generators/506e262f9354/tests/test_parametric_expansion_direction.py",
    "generators/506e262f9354/tests/test_parametric_promotion_adapter.py",
    "generators/506e262f9354/workspace/parametric/README.md",
    "generators/506e262f9354/workspace/parametric/adapter.py",
    "generators/506e262f9354/workspace/parametric/evidence/manifest.json",
    "generators/506e262f9354/workspace/parametric/promotion.json",
    "generators/506e262f9354/workspace/parametric/prototype.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_under(root: Path) -> dict[str, str]:
    result = {}
    for p in root.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc"):
            result[p.relative_to(root).as_posix()] = sha(p)
    return result


catalog = Catalog(REPO)
row = catalog.describe(TASK)
manifest_path = REPO / f"generators/{TASK}/workspace/parametric/evidence/manifest.json"
manifest = json.loads(manifest_path.read_text())
manifest_bad = []
for item in manifest["files"]:
    p = REPO / item["path"]
    if not p.is_file() or sha(p) != item["sha256"] or p.stat().st_size != item["bytes"]:
        manifest_bad.append(item["path"])

baseline_task = files_under(BASE / f"generators/{TASK}")
current_task = files_under(REPO / f"generators/{TASK}")
changed = sorted(
    f"generators/{TASK}/{name}"
    for name in set(baseline_task) | set(current_task)
    if baseline_task.get(name) != current_task.get(name)
)
writer = json.loads((WORK / "checks/final/writer-summary.json").read_text())
qualification = json.loads((WORK / "checks/final/qualification-summary.json").read_text())
api_ticket = json.loads((WORK / "checks/tickets/ticket-3b82645654e56bbf/result.json").read_text())
nvarc = json.loads((WORK / "checks/tickets/ticket-4fe545dfc6c52086/nvarc/skim-summary.json").read_text())
prototype_status = _prototype(REPO, row)
accepted = REPO / f"generators/{TASK}/parametric/accepted.json"
canonical_same = sha(BASE / "shared/data/canonical/puzzles.jsonl") == sha(REPO / "shared/data/canonical/puzzles.jsonl")

checks = {
    "generator_hash_unchanged": row["generator_sha256"] == EXPECTED_GENERATOR,
    "rule_hash_unchanged": row["rule_hash"] == EXPECTED_RULE,
    "canonical_program_hash_exact": qualification["canonical_default_sha256"] == EXPECTED_CANONICAL_PROGRAM,
    "canonical_data_unchanged": canonical_same,
    "prototype_current": prototype_status.get("status") == "current",
    "manifest_inventory_current": not manifest_bad,
    "changed_paths_exactly_scoped": changed == EXPECTED_CHANGED,
    "writer_public_batch_valid": all([
        writer["public_filenames_sorted"], writer["public_ids_unique"],
        writer["public_ids_match_exact_bytes"], writer["status"] == "proposed_unapproved",
    ]),
    "qualification_protected": qualification["status"] == "qualified"
        and qualification["racket"]["backend"] == "racket"
        and qualification["racket"]["protected"] is True
        and qualification["all_demo_only_survivors_unique"],
    "not_accepted": not accepted.exists(),
    "training_not_admitted": qualification["training_admitted"] is False,
    "api_ticket_passed": api_ticket["passed"] is True,
    "nvarc_ticket_passed": nvarc["predicted_ok"] is True and nvarc["bad_pairs"] == [],
}
report = {
    "task_id": TASK,
    "checks": checks,
    "passed": all(checks.values()),
    "changed_paths": changed,
    "expected_changed_paths": EXPECTED_CHANGED,
    "manifest_bad_paths": manifest_bad,
    "prototype_status": prototype_status,
    "generator_sha256": row["generator_sha256"],
    "rule_hash": row["rule_hash"],
    "parametric_status": {"status": "not_accepted", "training_admitted": False},
}
out = WORK / "checks/final/integrity.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["passed"] else 1)
