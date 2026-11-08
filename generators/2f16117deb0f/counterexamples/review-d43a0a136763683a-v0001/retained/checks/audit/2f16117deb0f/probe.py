from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "2f16117deb0f"
HERE = Path(__file__).resolve().parent
root = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)

grid = gen.generate(0, 0, difficulty="easy", texture="no_bank")
result = {
    "schema": "audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": source_sha256,
    "source_path": str(source_path.relative_to(root)),
    "recipe": {
        "seed": 0,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"texture": "no_bank"},
    },
    "dimensions": [len(grid), len(grid[0])],
    "self_check_without_meta": gen.self_check(grid),
    "self_check_with_meta": gen.self_check(grid, meta={"texture": "no_bank"}),
    "legend_nonzero": sum(value != 0 for value in grid[0]),
    "selector_nonzero": sum(value != 0 for value in grid[1]),
    "bank_key_nonzero": sum(value != 0 for value in grid[3]),
    "bank_entry_nonzero": sum(value != 0 for row in grid[4:6] for value in row),
    "published_invariants_violated": [
        "row 3 holds keys 1..K at non-overlapping column positions",
        "rows 4-5 hold 2x2 bank entries at the same column triples",
    ],
    "input": grid,
}
(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
