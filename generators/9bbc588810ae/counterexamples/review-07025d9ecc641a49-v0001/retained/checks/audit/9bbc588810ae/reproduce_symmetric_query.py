from pathlib import Path
import json
from reviewer_support import load_selected_generator

root = Path.cwd()
gen, _, _ = load_selected_generator("9bbc588810ae", root=root)

grid = [[0] * 23 for _ in range(5)]
for divider in (5, 11, 17):
    for row in range(5):
        grid[row][divider] = 9

# Panel 0 and the query are one-cell shapes, so panel 0 is the only matching
# source panel, but all seven transform codes match. Panels 1 and 2 have
# different cell counts and cannot match.
grid[1][1] = 1
for r, c in ((1, 1), (1, 2)):
    grid[r][6 + c] = 2
for r, c in ((0, 1), (1, 0), (1, 1), (1, 2)):
    grid[r][12 + c] = 3
grid[3][18 + 3] = 4

try:
    observed = gen.observe_axes(grid)
    observe_error = None
except Exception as exc:
    observed = None
    observe_error = f"{type(exc).__name__}: {exc}"

result = {
    "generator": "9bbc588810ae",
    "grid": grid,
    "query_cell_count": 1,
    "declared_query_cells": gen.AXES["query_cells"]["valid"],
    "self_check": gen.self_check(grid),
    "strict_canonical_like": gen.strict_canonical_like(grid),
    "panel0_matching_codes": list(gen._matching_codes(((0, 0),), ((0, 0),))),
    "observe_axes": observed,
    "observe_axes_error": observe_error,
    "rule_output": gen.rule_mirror(grid),
}
print(json.dumps(result, indent=2, sort_keys=True))
