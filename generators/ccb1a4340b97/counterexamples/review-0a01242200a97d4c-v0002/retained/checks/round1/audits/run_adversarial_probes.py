from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def l_windows(grid):
    found = []
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            values = [
                grid[row][col], grid[row][col + 1],
                grid[row + 1][col], grid[row + 1][col + 1],
            ]
            if values.count(8) == 3 and values.count(0) == 1:
                found.append((row, col))
    return found


module, path = load("60527b695836")
case = {
    "grid_h": 14,
    "grid_w": 16,
    "n_patterns": 4,
    "position_bias": "center",
    "L_variant_kind": "missing_BR",
    "separation": 2,
}
for seed in range(3):
    grid = module.generate(seed, 0, difficulty="hard", **case)
    print(json.dumps({
        "task": "60527b695836",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "seed": seed,
        "sample_index": 0,
        "overrides": case,
        "l_windows": l_windows(grid),
        "self_check": module.self_check(grid),
        "grid": grid,
    }, sort_keys=True))
for override in ({"anchor_corner": True}, {"asymmetry_force": True}, {"unknown_axis": 7}):
    try:
        grid = module.generate(11, 2, **override)
        result = {
            "task": "60527b695836",
            "override_probe": override,
            "accepted": True,
            "grid_sha": hashlib.sha256(json.dumps(grid).encode()).hexdigest(),
        }
    except Exception as exc:  # audit records either disposition
        result = {
            "task": "60527b695836",
            "override_probe": override,
            "accepted": False,
            "error": repr(exc),
        }
    print(json.dumps(result, sort_keys=True))

module, path = load("ccb1a4340b97")
blank = [[0] * 13 for _ in range(5)]
print(json.dumps({
    "task": "ccb1a4340b97",
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "probe": "blank_5x13",
    "self_check": module.self_check(blank),
    "grid": blank,
}, sort_keys=True))
base = module.generate(123, 0, difficulty="medium")
for override in (
    {"palette_kind": "warm"},
    {"palette_kind": "cool"},
    {"density": "sparse"},
    {"texture": "warm"},
    {"unknown_axis": 7},
):
    try:
        grid = module.generate(123, 0, difficulty="medium", **override)
        result = {
            "task": "ccb1a4340b97",
            "override_probe": override,
            "accepted": True,
            "same_as_default": grid == base,
            "grid_sha": hashlib.sha256(json.dumps(grid).encode()).hexdigest(),
        }
    except Exception as exc:
        result = {
            "task": "ccb1a4340b97",
            "override_probe": override,
            "accepted": False,
            "error": repr(exc),
        }
    print(json.dumps(result, sort_keys=True))
