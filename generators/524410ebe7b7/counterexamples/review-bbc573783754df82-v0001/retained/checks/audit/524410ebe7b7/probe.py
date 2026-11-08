from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "524410ebe7b7"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
SOURCE = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rectangle_only_rival(grid):
    """Fill interiors of complete axis-aligned hollow rectangle frames only."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r1 in range(h):
        for c1 in range(w):
            color = grid[r1][c1]
            if color == 0:
                continue
            for r2 in range(r1 + 2, h):
                for c2 in range(c1 + 2, w):
                    perimeter = (
                        all(grid[r][c1] == color and grid[r][c2] == color for r in range(r1, r2 + 1))
                        and all(grid[r1][c] == color and grid[r2][c] == color for c in range(c1, c2 + 1))
                    )
                    interior_zero = all(
                        grid[r][c] == 0
                        for r in range(r1 + 1, r2)
                        for c in range(c1 + 1, c2)
                    )
                    if perimeter and interior_zero:
                        for r in range(r1 + 1, r2):
                            for c in range(c1 + 1, c2):
                                out[r][c] = color
    return out


grid = json.loads((HERE / "input.json").read_text())
gen = load_generator()
rival = rectangle_only_rival(grid)
(HERE / "rival_output.json").write_text(json.dumps(rival, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "input_path": "checks/audit/524410ebe7b7/input.json",
    "self_check_errors": list(gen.self_check(deepcopy(grid))),
    "rival": "fill interiors of complete axis-aligned hollow rectangle frames only",
    "rival_output_path": "checks/audit/524410ebe7b7/rival_output.json",
    "rival_changed_cells": [
        [r, c, grid[r][c], rival[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != rival[r][c]
    ],
    "expected_authority_difference": "Racket also fills the cross-enclosed zero at (3,7) with 4; rectangle-only rival leaves it 0.",
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
