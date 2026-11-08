from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import traceback

from reviewer_support import find_root, load_selected_generator

TASK = "a61246736c26"
ROOT = find_root(__file__)
module, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def tile_copy(tile):
    return [row[:] for row in tile]


def put_tile(grid, parsed, row_index, col_index, tile):
    first_row, _ = parsed["row_bands"][row_index]
    first_col, _ = parsed["col_bands"][col_index]
    start_col = first_col + 1 if col_index == 0 else first_col
    for dr, values in enumerate(tile):
        for dc, value in enumerate(values):
            grid[first_row + dr][start_col + dc] = value


base = module.generate(3, 0, difficulty="easy", scene_profile="permuted_frames")
base_analysis = module._analysis(base)
parsed = module._source_parse(base)
accepted = copy.deepcopy(base)

# Move every column's sole solid tile into row band 0, swapping the row-0
# pattern copy back into the old solid row. This preserves exactly one solid
# plus two identical patterns in each column.
for col_index, old_solid_row in enumerate(base_analysis["solid_rows"]):
    if old_solid_row == 0:
        continue
    row0_tile = tile_copy(parsed["cores"][0][col_index])
    solid_tile = tile_copy(parsed["cores"][old_solid_row][col_index])
    put_tile(accepted, parsed, 0, col_index, solid_tile)
    put_tile(accepted, parsed, old_solid_row, col_index, row0_tile)

accepted_analysis = module._analysis(accepted)
actual = module.rule_mirror(accepted)
frame = accepted_analysis["row_colors"][0]
rival = [[0 if value == frame else value for value in row] for row in actual]
different_cells = [
    [r, c]
    for r in range(len(actual))
    for c in range(len(actual[0]))
    if actual[r][c] != rival[r][c]
]

# Current support check: all generated same-row cases should use frame 0.
same_row_generated = []
for band in ("easy", "medium", "hard"):
    for profile in module.GENERAL_PROFILES:
        for seed in range(12):
            grid = module.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
            analysis = module._analysis(grid)
            if len(set(analysis["solid_rows"])) == 1:
                row = analysis["solid_rows"][0]
                same_row_generated.append({
                    "band": band,
                    "profile": profile,
                    "seed": seed,
                    "solid_row": row,
                    "frame": analysis["row_colors"][row],
                })

malformed = copy.deepcopy(base)
malformed[5][0] = 9
malformed_exception = None
malformed_result = None
try:
    malformed_result = module.self_check(malformed)
except Exception as exc:  # evidence requires exact unhandled type/message
    malformed_exception = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "source_path": source_path.relative_to(ROOT).as_posix(),
    "source_sha256": source_sha256,
    "base": {
        "seed": 3,
        "sample_index": 0,
        "difficulty": "easy",
        "profile": "permuted_frames",
        "sha256": digest(base),
        "row_colors": list(base_analysis["row_colors"]),
        "solid_rows": list(base_analysis["solid_rows"]),
    },
    "accepted_counterexample": {
        "input_sha256": digest(accepted),
        "shape": [len(accepted), len(accepted[0])],
        "self_check": module.self_check(accepted),
        "observed_override": module.observe_overrides(accepted),
        "row_colors": list(accepted_analysis["row_colors"]),
        "solid_rows": list(accepted_analysis["solid_rows"]),
        "frame_selected": frame,
        "actual_output": actual,
        "same_row_force_zero_rival_output": rival,
        "different_cell_count": len(different_cells),
        "different_cells": different_cells,
        "input": accepted,
    },
    "generated_support_scan": {
        "explicit_draws": 3 * len(module.GENERAL_PROFILES) * 12,
        "same_row_draws": len(same_row_generated),
        "all_same_row_frames_zero": all(row["frame"] == 0 for row in same_row_generated),
        "same_row_examples": same_row_generated,
    },
    "malformed_counterexample": {
        "mutation": {"row": 5, "col": 0, "from": base[5][0], "to": 9},
        "input_sha256": digest(malformed),
        "self_check_result": malformed_result,
        "exception": malformed_exception,
        "input": malformed,
    },
    "findings": [
        "Accepted same-row nonzero-frame input refutes a rival that fits current generated same-row support.",
        "One separator-cell mutation makes self_check raise instead of returning structural errors.",
    ],
}
out = Path(__file__).with_name("evidence.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "out": str(out),
    "source_sha256": source_sha256,
    "accepted_self_check": report["accepted_counterexample"]["self_check"],
    "accepted_solid_rows": report["accepted_counterexample"]["solid_rows"],
    "accepted_frame": frame,
    "rival_difference_cells": len(different_cells),
    "same_row_draws": len(same_row_generated),
    "all_same_row_frames_zero": report["generated_support_scan"]["all_same_row_frames_zero"],
    "malformed_exception": malformed_exception and malformed_exception["type"],
}, indent=2))
assert report["accepted_counterexample"]["self_check"] == []
assert len(set(report["accepted_counterexample"]["solid_rows"])) == 1
assert frame != 0
assert different_cells
assert same_row_generated and all(row["frame"] == 0 for row in same_row_generated)
assert malformed_exception and malformed_exception["type"] == "IndexError"
