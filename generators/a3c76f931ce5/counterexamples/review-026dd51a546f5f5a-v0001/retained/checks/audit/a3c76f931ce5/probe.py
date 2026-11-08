#!/usr/bin/env python3
"""Reproduce dead/misdirected override controls for audit target a3c76f931ce5."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[4]
REPO = PACKET / "WORK" / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]
GENERATOR = REPO / "generators" / "a3c76f931ce5" / "generator.py"

spec = importlib.util.spec_from_file_location("audit_target", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def digest(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def hole_bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 0 < r < len(grid) - 1
        and 0 < c < len(row) - 1
        and value == 0
    ]
    return [
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    ]


fixed = {
    "grid_size": 10,
    "shape_color": 3,
    "hole_size": 2,
    "hole_position": "scattered",
}
seed = 173
sample_index = 11

dead_axes = {}
for axis in ("anchor_corner", "asymmetry_force"):
    cases = []
    for value in (False, True):
        grid = module.generate(
            seed,
            sample_index,
            difficulty="medium",
            **fixed,
            **{axis: value},
        )
        cases.append(
            {"value": value, "sha256": digest(grid), "hole_bbox": hole_bbox(grid)}
        )
    dead_axes[axis] = {
        "cases": cases,
        "identical": cases[0]["sha256"] == cases[1]["sha256"],
    }

default = module.generate(seed, sample_index, difficulty="medium", **fixed)
size_one = module.generate(
    seed,
    sample_index,
    difficulty="medium",
    **fixed,
    palette_size=1,
)
dead_axes["palette_size"] = {
    "cases": [
        {"value": "omitted", "sha256": digest(default)},
        {"value": 1, "sha256": digest(size_one)},
    ],
    "identical": digest(default) == digest(size_one),
}

kinds = ("warm", "cool", "broad", "primary")
perturbations = []
for probe_seed in range(32):
    cases = []
    for kind in kinds:
        grid = module.generate(
            probe_seed,
            sample_index,
            difficulty="medium",
            **fixed,
            palette_kind=kind,
        )
        cases.append(
            {
                "kind": kind,
                "sha256": digest(grid),
                "palette": sorted({value for row in grid for value in row}),
                "hole_bbox": hole_bbox(grid),
            }
        )
    if len({case["sha256"] for case in cases}) > 1:
        perturbations.append({"seed": probe_seed, "cases": cases})

result = {
    "task_id": "a3c76f931ce5",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "fixed_overrides": fixed,
    "dead_axes": dead_axes,
    "palette_kind_probe": {
        "seeds_checked": 32,
        "seeds_with_geometry_change_across_palette_kinds": len(perturbations),
        "all_realized_palettes": sorted(
            {
                tuple(case["palette"])
                for item in perturbations
                for case in item["cases"]
            }
        ),
        "first_counterexample": perturbations[0] if perturbations else None,
    },
    "finding": (
        "anchor_corner, asymmetry_force, and palette_size are byte-identical "
        "dead controls. palette_kind never changes the realized color set; it "
        "only changes hole geometry for some seeds because an unused palette "
        "shuffle consumes the shared layout RNG."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
