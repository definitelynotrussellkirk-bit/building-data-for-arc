"""Replay a production-plan lesson where a top-left-tile shortcut survives demos."""
from __future__ import annotations

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR = REPO / "generators" / "8dd7ace7de9a" / "generator.py"

spec = spec_from_file_location("audit_8dd7ace7de9a", GENERATOR)
assert spec and spec.loader
module = module_from_spec(spec)
spec.loader.exec_module(module)

SEED = 213_974_615_879_964
START = 66
DIFFICULTY = "easy"


def top_left_tile_shortcut(grid):
    """Recover the period sizes, but use only the first tile's cell values."""
    observed = module.observe_overrides(grid)
    period_r = observed["period_r"]
    period_c = observed["period_c"]
    tile = [row[:period_c] for row in grid[:period_r]]
    return [
        [tile[row % period_r][col % period_c] for col in range(len(grid[0]))]
        for row in range(len(grid))
    ]


rows = []
for offset in range(4):
    grid = module.generate(SEED, START + offset, difficulty=DIFFICULTY)
    expected = module.rule_mirror(grid)
    predicted = top_left_tile_shortcut(grid)
    differences = [
        [row, col, expected[row][col], predicted[row][col]]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if expected[row][col] != predicted[row][col]
    ]
    rows.append(
        {
            "offset": offset,
            "role": "demo" if offset < 3 else "query",
            "sample_index": START + offset,
            "observed_axes": module.observe_overrides(grid),
            "shortcut_matches": not differences,
            "difference_count": len(differences),
            "first_differences": differences[:10],
        }
    )

result = {
    "schema": "audit-reproduction-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": sha256(GENERATOR.read_bytes()).hexdigest(),
    "replay": {"difficulty": DIFFICULTY, "seed": SEED, "sample_index": START},
    "production_plan_note": (
        "This is pinned lesson-plan band easy, k=6: sample_index=k*11 and "
        "seed=sha256(profile-floor:v1:TASK:lesson:easy:k)[:12]."
    ),
    "shortcut": "infer period dimensions, then repeat the literal top-left tile",
    "pairs": rows,
    "demos_all_fit": all(row["shortcut_matches"] for row in rows[:3]),
    "query_differs": not rows[3]["shortcut_matches"],
    "finding": (
        "clean_anchor is random rather than lesson-scheduled, so three clean-anchor "
        "demonstrations can fail to teach recovery from noisy tile residues."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
