from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import find_root, load_selected_generator  # noqa: E402

TASK_ID = "65dc463a7236"
ROOT = find_root(REPO)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid):
    body = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def nonzero_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    queue.append((nr, nc))
    return count


def attempt(label, *, seed=19, sample_index=3, difficulty="medium", overrides=None):
    overrides = dict(overrides or {})
    row = {
        "label": label,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
    }
    try:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
        row.update(
            {
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": grid_sha(grid),
                "nonzero_cells": sum(value != 0 for line in grid for value in line),
                "nonzero_colors": sorted({value for line in grid for value in line if value != 0}),
                "nonzero_components_4": nonzero_components(grid),
                "self_check_default_meta": GEN.self_check(grid, difficulty=difficulty, meta={}),
                "self_check_with_meta": GEN.self_check(
                    grid, difficulty=difficulty, meta={"texture": overrides.get("texture", "")}
                ),
            }
        )
    except Exception as exc:  # reproducibility record
        row.update({"accepted": False, "exception": type(exc).__name__, "message": str(exc)})
    return row


attempts = [
    attempt("baseline"),
    attempt("unknown_axis_silently_accepted", overrides={"typo_axis": 123}),
    attempt("palette_size_1", overrides={"palette_size": 1}),
    attempt("palette_size_2", overrides={"palette_size": 2}),
    attempt("n_distinct_colors_1", overrides={"n_distinct_colors": 1}),
    attempt("n_distinct_colors_2", overrides={"n_distinct_colors": 2}),
    attempt("texture_default", overrides={"texture": "default"}),
    attempt("texture_warm", overrides={"texture": "warm"}),
    attempt("advertised_grid_h_min", overrides={"grid_h": 5}),
    attempt("advertised_grid_h_max", overrides={"grid_h": 16}),
    attempt("advertised_object_cells_min", overrides={"object_cells": 1}),
    attempt("advertised_object_cells_max", overrides={"object_cells": 20}),
    attempt("degenerate_multiple_objects", overrides={"texture": "multiple_objects"}),
]

by_label = {row["label"]: row for row in attempts}
baseline_sha = by_label["baseline"].get("grid_sha256")
for row in attempts:
    if row.get("accepted"):
        row["byte_identical_to_baseline"] = row.get("grid_sha256") == baseline_sha

payload = {
    "task_id": TASK_ID,
    "kind": "generator_contract_probe",
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "declared_rule_hash": getattr(GEN, "RULE_HASH", None),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/65dc463a7236/probe.py"],
    "payload_cwd": "repo",
    "attempts": attempts,
}
(HERE / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
