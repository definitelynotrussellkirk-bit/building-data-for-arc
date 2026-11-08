from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
TASK = "3ef9eae12446"
GEN = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Eight nonzero cells satisfy the current self_check, but this grid contains no
# hollow uniform 3x3 ring and therefore violates the documented ordinary domain.
grid = [
    [4, 4, 4, 4, 4, 4, 4],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [7, 0, 0, 0, 0, 0, 0],
]

def hollow_uniform_rings(g: list[list[int]]) -> list[dict[str, int]]:
    h, w = len(g), len(g[0])
    found: list[dict[str, int]] = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            border = [
                g[r0 + dr][c0 + dc]
                for dr in range(3)
                for dc in range(3)
                if (dr, dc) != (1, 1)
            ]
            if border[0] != 0 and len(set(border)) == 1 and g[r0 + 1][c0 + 1] == 0:
                found.append({"row": r0, "col": c0, "color": border[0]})
    return found

errors = mod.self_check(grid, difficulty="medium", meta={})
rings = hollow_uniform_rings(grid)
sha = hashlib.sha256(GEN.read_bytes()).hexdigest()
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": sha,
    "generator_version": mod.VERSION,
    "finding": "self_check accepts a grid with eight arbitrary nonzero cells but no documented hollow uniform 3x3 block",
    "input_shape": [len(grid), len(grid[0])],
    "nonzero_count": sum(v != 0 for row in grid for v in row),
    "hollow_uniform_rings": rings,
    "self_check_errors": errors,
    "validator_accepted": errors == [],
    "belongs_to_documented_ordinary_domain": bool(rings),
    "reproduced": errors == [] and not rings,
    "source_observation": "self_check only enforces nonzero_count >= 8 for non-degenerate inputs",
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["reproduced"] else 1)
