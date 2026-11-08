"""Verify the two assigned audit counterexamples against retained Racket outputs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator(task_id: str, expected_sha: str):
    path = REPO / "generators" / task_id / "generator.py"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == expected_sha, (task_id, actual, expected_sha)
    spec = importlib.util.spec_from_file_location(f"audit_verify_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(task_id: str) -> dict:
    base = HERE / task_id
    counter = json.loads((base / "counterexample.json").read_text())
    probe = json.loads((base / "probe.json").read_text())
    racket = json.loads((base / "racket.json").read_text())
    expected_sha = counter["source_sha256"]
    module = load_generator(task_id, expected_sha)
    inputs = probe["inputs"]
    intended = probe["independent_intended_outputs"]
    rivals = probe["rival_outputs"]
    demos = counter["demo_indices"]
    query = counter["query_index"]

    assert racket["generator_sha256"] == expected_sha
    assert racket["executed_rule_hash"] == counter["rule_hash"]
    assert len(racket["results"]) == len(inputs)
    racket_outputs = [row["output"] for row in racket["results"]]
    assert racket_outputs == intended
    assert all(module.self_check(grid, difficulty="easy") == [] for grid in inputs)
    assert all(rivals[index] == intended[index] for index in demos)
    differing = [
        (r, c)
        for r in range(len(intended[query]))
        for c in range(len(intended[query][r]))
        if rivals[query][r][c] != intended[query][r][c]
    ]
    assert len(differing) == counter["query_differing_cell_count"]
    assert differing
    return {
        "task_id": task_id,
        "source_sha256": expected_sha,
        "rule_hash": counter["rule_hash"],
        "ordinary_generator_window": True,
        "validator_accepts": True,
        "demonstrations": len(demos),
        "rival_name": counter["rival_name"],
        "rival_fits_all_demonstrations": True,
        "query_differing_cell_count": len(differing),
        "racket_outputs_match_independent_mirror": True,
    }


report = {
    "schema": "arcpuzzles-audit-verification-v1",
    "status": "pass",
    "findings": [verify("13a5c3f25c60"), verify("2082a4577cff")],
}
(HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
