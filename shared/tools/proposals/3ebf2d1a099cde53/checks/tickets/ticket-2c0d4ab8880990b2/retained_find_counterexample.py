from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "0c2ab7de69d1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def intended_python(grid):
    return module._mirror(grid)


def overwrite_rival(grid):
    """Reflect every eligible above cell even when its target is occupied."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0])
    d = next((r for r in range(h) if all(v == 5 for v in grid[r])), None)
    if d is None:
        return out
    for r in range(d):
        for c in range(w):
            value = grid[r][c]
            target_r = 2 * d - r
            if value not in (0, 5) and 0 <= target_r < h:
                out[target_r][c] = 8
    return out


def classify(grid):
    intended = intended_python(grid)
    rival = overwrite_rival(grid)
    differing = [
        [r, c, intended[r][c], rival[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if intended[r][c] != rival[r][c]
    ]
    return intended, rival, differing


found = None
for seed in range(5000):
    grids = [module.generate(seed, i, difficulty="medium") for i in range(4)]
    rows = []
    for i, grid in enumerate(grids):
        intended, rival, differing = classify(grid)
        rows.append(
            {
                "sample_index": i,
                "self_check_errors": module.self_check(grid, difficulty="medium", meta={}),
                "rival_agrees": not differing,
                "differences": differing,
            }
        )
    if all(row["rival_agrees"] and not row["self_check_errors"] for row in rows[:3]) \
            and (not rows[3]["rival_agrees"]) and not rows[3]["self_check_errors"]:
        found = (seed, grids, rows)
        break

if found is None:
    raise SystemExit("no counterexample found in seeds 0..4999")

seed, grids, rows = found
rivals = [overwrite_rival(grid) for grid in grids]
source_sha = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()

(HERE / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
(HERE / "rival_outputs.json").write_text(json.dumps(rivals, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-lesson-counterexample-v1",
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "seed": seed,
    "difficulty": "medium",
    "demonstration_sample_indices": [0, 1, 2],
    "query_sample_index": 3,
    "rival": "Reflect eligible above-divider cells even when the reflected target is occupied (overwrite blockers).",
    "demonstrations_fit_rival_python_mirror": [row["rival_agrees"] for row in rows[:3]],
    "query_disagrees_python_mirror": not rows[3]["rival_agrees"],
    "query_differences_python_mirror": rows[3]["differences"],
    "all_inputs_pass_self_check": all(not row["self_check_errors"] for row in rows),
    "lesson_policy": "same seed, normal sampler, sample indices 0..2 as three demonstrations and index 3 as query",
    "instances": rows,
    "input_path": "checks/audit/0c2ab7de69d1/input.json",
    "rival_outputs_path": "checks/audit/0c2ab7de69d1/rival_outputs.json",
}
(HERE / "search_report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
