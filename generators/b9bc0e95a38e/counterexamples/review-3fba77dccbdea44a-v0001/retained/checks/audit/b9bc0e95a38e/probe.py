#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
TASK = "b9bc0e95a38e"
SOURCE = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_b9", SOURCE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

invalid = [
    {"n_seeds": 2}, {"palette_size": 9}, {"seed_kind": "multi"},
    {"palette_kind": "nonsense"}, {"anchor_corner": "yes"},
    {"asymmetry_force": 7}, {"texture": "nonsense"},
]
invalid_results = []
for overrides in invalid:
    try:
        grid = mod.generate(1, 2, **overrides)
        invalid_results.append({
            "overrides": overrides,
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "seed_count": sum(value == 8 for row in grid for value in row),
            "self_check": mod.self_check(grid),
        })
    except Exception as exc:
        invalid_results.append({"overrides": overrides, "accepted": False,
                                "error": f"{type(exc).__name__}: {exc}"})

baseline = mod.generate(1, 2)
inert = []
for overrides in [
    {"n_seeds": 1}, {"palette_size": 1}, {"seed_kind": "single"},
    {"palette_kind": "fixed"}, {"anchor_corner": True},
    {"asymmetry_force": True},
]:
    candidate = mod.generate(1, 2, **overrides)
    inert.append({"overrides": overrides, "byte_equal_to_default": candidate == baseline})

malformed = []
for name, value in [("none", None), ("integer", 42), ("ragged", [[0], [0, 8]])]:
    try:
        malformed.append({"case": name, "returned": mod.self_check(value), "crashed": False})
    except Exception as exc:
        malformed.append({"case": name, "crashed": True,
                          "error": f"{type(exc).__name__}: {exc}"})

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "invalid_override_cases": invalid_results,
    "declared_axis_inertness": inert,
    "malformed_validator_cases": malformed,
    "finding": (
        "Seven invalid controls are accepted and produce self_check-clean one-seed grids; "
        "six advertised controls are byte-identical to the default at the same seed/index; "
        "self_check crashes on None and integer inputs."
    ),
}
Path(__file__).with_name("result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
