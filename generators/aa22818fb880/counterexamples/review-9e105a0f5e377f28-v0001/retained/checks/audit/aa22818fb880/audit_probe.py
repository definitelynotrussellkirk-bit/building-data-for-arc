from __future__ import annotations

from pathlib import Path
import copy
import json

from reviewer_support import find_root, load_selected_generator

TASK_ID = "aa22818fb880"
ROOT = find_root(Path.cwd())
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def partial_centers(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            same = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == color:
                    same.append((dr, dc))
            if len(same) == 3:
                result.append((r, c, color))
    return result


def local_rule(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r, c, color in partial_centers(grid):
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or grid[rr][cc] != color:
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                    out[rr][cc] = color
                break
    return out


def global_count_four_rival(grid: list[list[int]]) -> list[list[int]]:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value:
                counts[value] = counts.get(value, 0) + 1
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r, c, color in partial_centers(grid):
        if counts[color] != 4:
            continue
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or grid[rr][cc] != color:
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                    out[rr][cc] = color
                break
    return out


sample_rows = []
all_rival_match = True
all_center_colors_have_global_count_four = True
for band in ("easy", "medium", "hard"):
    matches = 0
    exact_four = 0
    generated_centers = 0
    for seed in range(100):
        grid = GEN.generate(seed, seed * 101 + 19, difficulty=band)
        centers = partial_centers(grid)
        generated_centers += len(centers)
        counts: dict[int, int] = {}
        for row in grid:
            for value in row:
                if value:
                    counts[value] = counts.get(value, 0) + 1
        this_exact = all(counts[color] == 4 for _, _, color in centers)
        this_match = global_count_four_rival(grid) == local_rule(grid)
        exact_four += int(this_exact)
        matches += int(this_match)
        all_center_colors_have_global_count_four &= this_exact
        all_rival_match &= this_match
    sample_rows.append(
        {
            "band": band,
            "draws": 100,
            "draws_where_every_center_color_count_is_four": exact_four,
            "rival_matches_local_rule": matches,
            "total_partial_centers": generated_centers,
        }
    )

underfilled = GEN.generate(3, 0, difficulty="easy", n_motifs=2)
underfilled_centers = partial_centers(underfilled)
underfilled_self_check = GEN.self_check(underfilled, difficulty="easy")

try:
    GEN.generate(1, 0, difficulty="easy", grid_h=5)
except Exception as exc:  # evidence records exact public behavior
    grid_h_5 = {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}
else:
    grid_h_5 = {"accepted": True}

try:
    unknown_grid = GEN.generate(1, 0, difficulty="easy", typo_axis=123)
except Exception as exc:
    unknown_override = {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}
else:
    unknown_override = {
        "accepted": True,
        "grid_shape": [len(unknown_grid), len(unknown_grid[0])],
    }

counterexample = [
    [3, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 3, 3, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
local = local_rule(counterexample)
rival = global_count_four_rival(counterexample)

assert len(underfilled_centers) == 1
assert underfilled_self_check == []
assert not grid_h_5["accepted"]
assert unknown_override["accepted"]
assert all_center_colors_have_global_count_four
assert all_rival_match
assert local != rival

report = {
    "schema": "arc-audit-partial-plus-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE_PATH.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "underfilled_exact_override": {
        "command": "generate(3, 0, difficulty='easy', n_motifs=2)",
        "requested_motifs": 2,
        "observed_centers": len(underfilled_centers),
        "self_check_errors": underfilled_self_check,
        "grid": underfilled,
    },
    "declared_grid_h_5": grid_h_5,
    "unknown_override": unknown_override,
    "generated_shortcut_sample": {
        "seed_range": [0, 99],
        "sample_index_formula": "seed * 101 + 19",
        "total_draws": 300,
        "all_center_colors_have_global_count_four": all_center_colors_have_global_count_four,
        "global_count_four_rival_matches_local_rule": all_rival_match,
        "bands": sample_rows,
    },
    "shortcut_counterexample": {
        "description": "An extra isolated 3 raises the global color count to five without changing the valid local partial plus.",
        "input": counterexample,
        "local_rule_output": local,
        "global_count_four_rival_output": rival,
        "rival_disagrees": local != rival,
    },
}
print(json.dumps(report, indent=2, sort_keys=True))
