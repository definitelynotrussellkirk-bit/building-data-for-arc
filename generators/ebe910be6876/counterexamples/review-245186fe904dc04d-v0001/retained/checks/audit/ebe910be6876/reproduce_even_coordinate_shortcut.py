from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "ebe910be6876"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = ROOT / "generators" / TASK / "generator.py"
OUT = Path(__file__).with_name("even_coordinate_shortcut.json")

spec = importlib.util.spec_from_file_location("audited_ebe", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def expand(grid, snapped=False):
    h, w = len(grid), len(grid[0])
    out = [[0]*(2*w) for _ in range(2*h)]
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if not color: continue
            if snapped:
                sr, sc = 4*(r//2), 4*(c//2)
            else:
                sr, sc = 2*r-2, 2*c-2
            for rr in range(sr, sr+4):
                for cc in range(sc, sc+4):
                    if 0 <= rr < 2*h and 0 <= cc < 2*w:
                        out[rr][cc] = color
    return out

calls = matches = 0
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = module.generate(20000 + index, index, difficulty=band)
        calls += 1
        matches += int(expand(grid, False) == expand(grid, True))

counterexample = [[0]*6 for _ in range(6)]
for r,c,color in ((1,1,1),(1,5,2),(5,1,4),(2,2,3)):
    counterexample[r][c] = color
intended = expand(counterexample, False)
rival = expand(counterexample, True)
differences = [
    [r,c,intended[r][c],rival[r][c]]
    for r in range(12) for c in range(12)
    if intended[r][c] != rival[r][c]
]
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "claim": "Odd-only training cannot distinguish 2r-2 placement from snapping to the logical odd lattice.",
    "generated_calls": calls,
    "shortcut_matches": matches,
    "all_generated_matched": matches == calls,
    "counterexample_input": counterexample,
    "generator_self_check_errors": module.self_check(counterexample),
    "intended_output": intended,
    "snapped_rival_output": rival,
    "difference_count": len(differences),
    "first_differences": differences[:20],
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k:v for k,v in report.items() if k not in ("counterexample_input","intended_output","snapped_rival_output","first_differences")}, indent=2))
