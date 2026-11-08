from __future__ import annotations
import json, os, sys
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "28119d6d0e10"
SEED = 57
START = 6
OVERRIDES = {"grid_h": 8}
root = find_root(__file__)
gen, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)

def reading_order_rival(grid):
    analysis = gen._analysis(grid)
    out = [list(row) for row in grid]
    for color, component in zip(
        analysis["legend"], sorted(analysis["components"], key=lambda c: c["first"])
    ):
        for row, col in component["cells"]:
            out[row][col] = color
    return out

grids = [
    gen.generate(SEED, START + offset, difficulty="medium", **OVERRIDES)
    for offset in range(4)
]
rule_outputs = [gen.rule_mirror(grid) for grid in grids]
rival_outputs = [reading_order_rival(grid) for grid in grids]
match = [a == b for a, b in zip(rule_outputs, rival_outputs, strict=True)]
self_checks = [
    gen.self_check(grid, difficulty="medium", meta={"overrides": OVERRIDES})
    for grid in grids
]
analysis = [
    {
        "sample_index": START + offset,
        "n_shapes": gen._analysis(grid)["n_shapes"],
        "reading_order_sizes": [
            component["size"]
            for component in sorted(
                gen._analysis(grid)["components"], key=lambda c: c["first"]
            )
        ],
    }
    for offset, grid in enumerate(grids)
]
out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
payload = {
    "schema": "arc-audit-reading-order-survivor-v1",
    "task_id": TASK_ID,
    "generator_path": str(generator_path),
    "generator_sha256": generator_sha256,
    "seed": SEED,
    "start_sample_index": START,
    "difficulty": "medium",
    "overrides": OVERRIDES,
    "lesson_policy": "three consecutive demonstrations followed by one query",
    "inputs": grids,
    "python_rule_outputs": rule_outputs,
    "reading_order_rival_outputs": rival_outputs,
    "rival_matches_selected_rule": match,
    "self_check_errors": self_checks,
    "analysis": analysis,
    "finding": (
        "The benign exact grid_h override bypasses _matches_lesson_phase; "
        "reading-order recoloring matches all three demonstrations but differs on the query."
    ),
    "command": {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]},
    "passed_reproducer": match[:3] == [True, True, True] and match[3] is False and not any(self_checks),
}
(out_dir / "reading-order-survivor.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({"passed_reproducer": payload["passed_reproducer"], "match": match, "generator_sha256": generator_sha256}))
raise SystemExit(0 if payload["passed_reproducer"] else 1)
