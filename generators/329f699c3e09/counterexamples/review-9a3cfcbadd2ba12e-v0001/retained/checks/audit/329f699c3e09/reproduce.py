from __future__ import annotations
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
TASK = "329f699c3e09"
SOURCE = WORK / "repo" / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_target_329", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

grid = GEN.generate(21, 0, difficulty="easy")
assert GEN.self_check(grid) == []
h, w = len(grid), len(grid[0])
full_rows = [r for r in range(h) if all(grid[r][c] == 7 for c in range(w))]
full_cols = [c for c in range(w) if all(grid[r][c] == 7 for r in range(h))]
assert len(full_rows) + len(full_cols) == 1

rival = deepcopy(grid)
collisions = []
for r in range(h):
    for c in range(w):
        if grid[r][c] != 6:
            continue
        if full_cols:
            nr, nc = r, 2 * full_cols[0] - c
        else:
            nr, nc = 2 * full_rows[0] - r, c
        if 0 <= nr < h and 0 <= nc < w:
            if grid[nr][nc] == 0:
                rival[nr][nc] = 8
            elif grid[nr][nc] not in (6, 7):
                collisions.append({
                    "source": [r, c],
                    "destination": [nr, nc],
                    "overwritten_input_color": grid[nr][nc],
                })

assert collisions == [{
    "source": [0, 5],
    "destination": [6, 5],
    "overwritten_input_color": 5,
}]
actual = json.loads((Path(__file__).parent / "racket.json").read_text())["results"][0]["output"]
assert actual[6][5] == 8
assert rival[6][5] == 5

result = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 21,
    "sample_index": 0,
    "difficulty": "easy",
    "self_check": [],
    "collisions": collisions,
    "actual_racket_output": actual,
    "preserve_occupied_destination_rival_output": rival,
    "finding": (
        "The documented claim that distractors are preserved is false for this "
        "accepted generated input: a magenta reflection overwrites color 5 with 8."
    ),
}
(Path(__file__).parent / "counterexample.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({"passed": True, "collisions": collisions}, sort_keys=True))
