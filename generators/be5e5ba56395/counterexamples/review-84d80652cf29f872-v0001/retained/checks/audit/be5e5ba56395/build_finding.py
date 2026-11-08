from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
TASK = "be5e5ba56395"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_gen", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

input_grid = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
actual = racket["results"][0]["output"]

# Plausible domain-respecting rival: outline only components that are already
# solid rectangles; leave malformed components unchanged instead of inventing
# their missing bounding-box cells.
def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out

rival = deepcopy(input_grid)
for color, cells in components(input_grid):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    solid = len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)
    if not solid:
        continue
    for r, c in cells:
        if r not in (r0, r1) and c not in (c0, c1):
            rival[r][c] = 0

changed = [
    [r, c, rival[r][c], actual[r][c]]
    for r in range(len(input_grid))
    for c in range(len(input_grid[0]))
    if rival[r][c] != actual[r][c]
]

finding = {
    "schema": "arc-review-audit-counterexample-v1",
    "task_id": TASK,
    "generator_version": gen.VERSION,
    "generator_sha256": racket["generator_sha256"],
    "rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "documented_domain": "every colored component is a filled axis-aligned rectangle",
    "validator_errors": gen.self_check(input_grid),
    "validator_accepts": gen.self_check(input_grid) == [],
    "input": input_grid,
    "actual_racket_output": actual,
    "rival_output_outline_only_solid_components": rival,
    "differing_cells_r_c_rival_actual": changed,
    "finding": (
        "self_check accepts a grid containing one valid 3x3 rectangle plus a nonrectangular L component. "
        "The selected rule then outlines the L's bounding box and invents three cells, while a domain-respecting "
        "interpretation leaves the malformed component unchanged."
    ),
    "apply_command": racket["command"],
    "apply_cwd": racket["cwd"],
    "reproducer": "python3 checks/audit/be5e5ba56395/build_finding.py (from packet root with runtime on PYTHONPATH)",
}
(HERE / "finding.json").write_text(json.dumps(finding, indent=2) + "\n")
print(json.dumps({"validator_errors": finding["validator_errors"], "differing_cells": changed}, indent=2))
