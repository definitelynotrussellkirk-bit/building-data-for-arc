#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK = "c1fd38e5812b"
OUT = HERE.parent
GEN, SOURCE, DIGEST = load_selected_generator(TASK, root=REPO)


def expand(logical: list[list[int]], row_spans: list[int], col_spans: list[int]) -> list[list[int]]:
    return [
        [value for value, width in zip(logical_row, col_spans) for _ in range(width)]
        for logical_row, height in zip(logical, row_spans)
        for _ in range(height)
    ]


def starts(values: list[int]) -> list[int]:
    return [0] + [index for index in range(1, len(values)) if values[index] != values[index - 1]]


def rival(grid: list[list[int]]) -> list[list[int]]:
    row_starts = starts([row[0] for row in grid])
    row_spans = [b - a for a, b in zip(row_starts, row_starts[1:] + [len(grid)])]
    if len(set(row_spans)) == 1:
        first_width = next(
            (col for col in range(1, len(grid[0])) if grid[0][col] != grid[0][col - 1]),
            len(grid[0]),
        )
        col_starts = list(range(0, len(grid[0]), first_width))
    else:
        col_starts = starts(grid[0])
    return [[grid[row][col] for col in col_starts] for row in row_starts]


logical = [[0, 1], [2, 2], [3, 3], [0, 1], [2, 2], [3, 3]]
row_spans = [2, 2, 2, 2, 2, 2]
col_spans = [4, 8]
grid = expand(logical, row_spans, col_spans)
expected = GEN.solve_python(grid)
rival_output = rival(grid)
assert expected == logical
assert rival_output == [[0, 1, 1], [2, 2, 2], [3, 3, 3], [0, 1, 1], [2, 2, 2], [3, 3, 3]]
assert GEN.self_check(grid) == []
assert GEN.observe_overrides(grid) == {"scene_profile": "interior_merges"}
assert expected != rival_output

(OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
record = {
    "schema": "arcpuzzles-audit-probe-preapply-v1",
    "task_id": TASK,
    "generator_sha256": DIGEST,
    "source_path": str(SOURCE.relative_to(REPO)),
    "prior_audit_lead": "review-b24d187658115e8e:v0001",
    "construction": {
        "logical": logical,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "input_shape": [len(grid), len(grid[0])],
    },
    "generator_domain": {
        "self_check_errors": GEN.self_check(grid),
        "observed_overrides": GEN.observe_overrides(grid),
    },
    "python_authority_mirror": expected,
    "rival_name": "couple_column_uniformity_to_uniform_row_spans",
    "rival_output": rival_output,
    "apply_command": {
        "cwd": "WORK",
        "argv": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", f"../checks/audit/{TASK}/input.json", "--check-generator-domain",
            "--out", f"../checks/audit/{TASK}/racket.json",
        ],
    },
}
(OUT / "probe-preapply.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({"task_id": TASK, "generator_sha256": DIGEST, "self_check": [], "rival_differs": True}, sort_keys=True))
