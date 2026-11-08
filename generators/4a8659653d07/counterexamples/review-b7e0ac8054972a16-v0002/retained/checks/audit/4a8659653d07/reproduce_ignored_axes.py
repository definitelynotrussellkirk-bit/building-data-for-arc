#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK_ID = "4a8659653d07"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def active_columns(grid):
    return [c for c in range(len(grid[0])) if any(row[c] != 0 for row in grid)]

seed, sample_index = 123, 5
two = mod.generate(seed, sample_index, n_active_cols=2, palette_size=1)
ten = mod.generate(seed, sample_index, n_active_cols=10, palette_size=9)
reported_error = None
try:
    mod.generate(seed, sample_index, grid_h=12, grid_w=12)
except Exception as exc:
    reported_error = f"{type(exc).__name__}: {exc}"
result = {
    "schema": "arcpuzzles-adversarial-audit-repro-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "advertised_n_active_cols_valid": "2..10",
    "advertised_palette_size_valid": "1..9",
    "requested_a": {"n_active_cols": 2, "palette_size": 1},
    "requested_b": {"n_active_cols": 10, "palette_size": 9},
    "outputs_identical": two == ten,
    "observed_active_columns": active_columns(two),
    "observed_non_background_colors": sorted({x for row in two for x in row if x}),
    "advertised_grid_shape_request": [12, 12],
    "grid_shape_request_error": reported_error,
    "grid": two,
}
print(json.dumps(result, indent=2))
