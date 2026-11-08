#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK_ID = "63f85ac336c1"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def component_count(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc)); stack.append((nr, nc))
    return count

seed, sample_index = 123, 5
one = mod.generate(seed, sample_index, n_components=1)
five = mod.generate(seed, sample_index, n_components=5)
reported_error = None
try:
    mod.generate(seed, sample_index, grid_h=14, grid_w=16)
except Exception as exc:
    reported_error = f"{type(exc).__name__}: {exc}"
result = {
    "schema": "arcpuzzles-adversarial-audit-repro-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "advertised_n_components_valid": "1..5",
    "requested": [1, 5],
    "outputs_identical": one == five,
    "observed_component_count": component_count(one),
    "advertised_grid_shape_request": [14, 16],
    "grid_shape_request_error": reported_error,
    "grid": one,
}
print(json.dumps(result, indent=2))
