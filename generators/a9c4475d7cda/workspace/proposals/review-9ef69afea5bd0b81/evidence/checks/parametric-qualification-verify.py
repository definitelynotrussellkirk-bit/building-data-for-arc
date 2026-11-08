#!/usr/bin/env python3
"""Compact, source-bound verification of the retained qualification artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "parametric" / "a9c4475d7cda-qualification-v1"
QUALIFICATION = EVIDENCE / "qualification.json"
EXECUTION = EVIDENCE / "execution.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


qualification = json.loads(QUALIFICATION.read_text())
execution = json.loads(EXECUTION.read_text())

assert sha256(QUALIFICATION) == "463dfb54fe21b8cb9c82baff8869be621568f7446e2e276c421af9bba40377a6"
assert sha256(EXECUTION) == "f3391a611b206ce3df3dab7158eb380b97a51f1f60ab1c9e7ef0a44ed2f7b7d4"
assert qualification["schema"] == "arcpuzzles-parametric-qualification-v1"
assert qualification["task_id"] == "a9c4475d7cda"
assert qualification["status"] == "qualified"
assert qualification["training_admitted"] is False
assert qualification["execution"] == {
    "path": "execution.json",
    "sha256": "f3391a611b206ce3df3dab7158eb380b97a51f1f60ab1c9e7ef0a44ed2f7b7d4",
}
expected_programs = {
    '{"panel_threshold":1}': "f271048a7d3365bf0bb2ada65cf226643bb2671dda85b3747dca7697f6d19278",
    '{"panel_threshold":2}': "4e6231455ecb950b5c408077976da1f2ee06d3b29707dbbd2717e6cdbbeb6668",
    '{"panel_threshold":3}': "dc31cbe125fa65b167cd9399fbb5595983d12d20d22c31dd8931ce6377ba2522",
}
assert qualification["programs"] == expected_programs
jobs = qualification["jobs"]
assert len(jobs) == 6
assert {
    (job["settings"]["panel_threshold"], job["seed"], job["demos"], job["queries"])
    for job in jobs
} == {
    (threshold, seed, 3, 4)
    for threshold in (1, 2, 3)
    for seed in (0, 17)
}
assert execution["racket_evaluations"] == 78
assert len(execution["checks"]) == 6
assert len(execution["episodes"]) == 6
assert all(
    check["survivors"] == [check["settings"]]
    and check["counts"] == {"demos": 3, "queries": 4}
    and check["label_count"] == 7
    for check in execution["checks"]
)
assert qualification["source_binding"]["generator_sha256"] == (
    "1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51"
)

print(json.dumps({
    "status": "pass",
    "task_id": qualification["task_id"],
    "qualified_jobs": len(jobs),
    "thresholds": [1, 2, 3],
    "seeds_per_threshold": [0, 17],
    "demos_per_job": 3,
    "queries_per_job": 4,
    "racket_evaluations": execution["racket_evaluations"],
    "canonical_program_sha256": expected_programs['{"panel_threshold":2}'],
    "variant_approved": False,
    "training_admitted": qualification["training_admitted"],
}, sort_keys=True))
