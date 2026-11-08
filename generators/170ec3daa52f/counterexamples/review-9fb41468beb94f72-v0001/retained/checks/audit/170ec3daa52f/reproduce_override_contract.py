#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
SOURCE = REPO / "generators" / "170ec3daa52f" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_170ec3daa52f", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def digest_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def summarize(grid):
    return {
        "shape": [len(grid), len(grid[0])],
        "palette": sorted({v for row in grid for v in row}),
        "grid_sha256": digest_grid(grid),
        "self_check": mod.self_check(grid),
        "grid": grid,
    }

advertised = {
    "grid_h": 4, "grid_w": 14, "palette_kind": "default", "variant": 0,
    "palette_size": 4, "position_bias": "three_panels_separated_by_8",
    "n_distinct_colors": 4, "density": "dense",
}
grid = mod.generate(0, 0, difficulty="medium", **advertised)
unknown = mod.generate(0, 0, difficulty="medium", typo_axis=1)
variant0 = mod.generate(19, 3, difficulty="hard", variant=0)
variant2 = mod.generate(19, 3, difficulty="hard", variant=2)
report = {
    "schema": "arcpuzzles-audit-override-counterexample-v1",
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": mod.VERSION,
    "cases": {
        "advertised_controls": {"call": {"seed": 0, "sample_index": 0, "difficulty": "medium", **advertised}, **summarize(grid)},
        "unknown_key_accepted": {"call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "typo_axis": 1}, **summarize(unknown)},
        "variant_zero": {"call": {"seed": 19, "sample_index": 3, "difficulty": "hard", "variant": 0}, **summarize(variant0)},
        "variant_two": {"call": {"seed": 19, "sample_index": 3, "difficulty": "hard", "variant": 2}, **summarize(variant2)},
    },
    "observations": {
        "requested_shape": [4, 14],
        "returned_shape": [len(grid), len(grid[0])],
        "shape_override_ignored": [len(grid), len(grid[0])] != [4, 14],
        "unknown_key_validator_clean": mod.self_check(unknown) == [],
        "variant_outputs_identical": variant0 == variant2,
    },
    "prior_source_matching_audit": "generators/170ec3daa52f/evidence/review_index.json",
    "command": ["python3", "checks/audit/170ec3daa52f/reproduce_override_contract.py"],
    "working_directory": str(WORK),
}
OUT = HERE.with_name("override-contract-counterexample.json")
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["observations"], indent=2))
if not all((report["observations"]["shape_override_ignored"],
            report["observations"]["unknown_key_validator_clean"],
            report["observations"]["variant_outputs_identical"])):
    raise SystemExit(1)
