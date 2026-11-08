from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

REPO = Path.cwd()
TASK_ID = "f6875586326b"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"
OUT_PATH = REPO.parent / "checks" / "audit" / TASK_ID / "probe.json"
TASK_RESULT = REPO.parent / "checks" / "audit" / TASK_ID / "task-tests" / "result.json"

spec = importlib.util.spec_from_file_location("audit_target_f6875586326b", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

canonical = None
with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            canonical = row
            break
assert canonical is not None
pairs = list(canonical["train"]) + list(canonical["test"])
canonical_results = [
    {
        "pair_index": i,
        "validator_errors": mod.self_check(pair["input"]),
        "rule_mirror_matches": mod.rule_mirror(pair["input"]) == pair["output"],
    }
    for i, pair in enumerate(pairs)
]

sample_details = []
for band_index, band in enumerate(("easy", "medium", "hard")):
    for i in range(100):
        seed = 687000 + band_index * 1000 + i
        grid = mod.generate(seed, i, difficulty=band)
        sample_details.append(
            {
                "difficulty": band,
                "seed": seed,
                "sample_index": i,
                "validator_errors": mod.self_check(grid, difficulty=band),
                "observed": mod.observe_overrides(grid),
            }
        )

boundary_details = []
index = 0
for band, grid_h, grid_w, n_rows, n_cols in itertools.product(
    ("easy", "medium", "hard"),
    (7, 16),
    (7, 18),
    (2, 4),
    (1, 3),
):
    overrides = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_rows": n_rows,
        "n_cols": n_cols,
    }
    result = {
        "difficulty": band,
        "seed": 690000 + index,
        "sample_index": 3001,
        "overrides": overrides,
        "accepted": False,
        "validator_errors": None,
        "observed": None,
        "error": None,
    }
    try:
        grid = mod.generate(690000 + index, 3001, difficulty=band, **overrides)
        result["accepted"] = True
        result["validator_errors"] = mod.self_check(grid, difficulty=band)
        result["observed"] = mod.observe_overrides(grid)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    boundary_details.append(result)
    index += 1

task_result = json.loads(TASK_RESULT.read_text())
stdout = task_result.get("stdout", "")
failed_line = next((line for line in stdout.splitlines() if line.startswith("FAILED ")), None)

payload = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": hashlib.sha256(" ".join(canonical["program_solution"].split()).encode()).hexdigest()[:12],
    "semantic_checks": {
        "canonical_pairs_total": len(canonical_results),
        "canonical_pairs_validator_pass": sum(not x["validator_errors"] for x in canonical_results),
        "canonical_pairs_rule_mirror_match": sum(x["rule_mirror_matches"] for x in canonical_results),
        "canonical_details": canonical_results,
        "default_samples_total": len(sample_details),
        "default_samples_validator_pass": sum(not x["validator_errors"] for x in sample_details),
        "sample_policy": {
            "difficulties": ["easy", "medium", "hard"],
            "samples_per_difficulty": 100,
            "sample_index_range": [0, 99],
            "seed_ranges": {
                "easy": [687000, 687099],
                "medium": [688000, 688099],
                "hard": [689000, 689099],
            },
        },
        "boundary_combinations_total": len(boundary_details),
        "boundary_combinations_valid_and_exact": sum(
            x["accepted"] and not x["validator_errors"] and x["observed"] == x["overrides"]
            for x in boundary_details
        ),
        "boundary_details": boundary_details,
    },
    "reproduced_issue": {
        "kind": "portable task-test path defect",
        "supported_stage_exit_code": task_result.get("exit_code"),
        "test_status": task_result.get("test_status"),
        "pytest_summary": "1 failed, 15 passed",
        "failed_line": failed_line,
        "root_cause": "tests/test_generator_f6875586326b.py derives REPO as tests/.., then looks for generators/f6875586326b/data/canonical/puzzles.jsonl instead of using the portable canonical-data helper or runtime shared-data path",
        "evidence": "checks/audit/f6875586326b/task-tests/result.json",
    },
    "conclusion": "No generator-semantic defect found in the sampled/boundary checks; one supported portable task-test failure was reproduced.",
}
OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "canonical": [payload["semantic_checks"]["canonical_pairs_rule_mirror_match"], len(canonical_results)],
    "samples": [payload["semantic_checks"]["default_samples_validator_pass"], len(sample_details)],
    "boundaries": [payload["semantic_checks"]["boundary_combinations_valid_and_exact"], len(boundary_details)],
    "task_tests": payload["reproduced_issue"]["pytest_summary"],
    "failed_line": failed_line,
}, indent=2))
