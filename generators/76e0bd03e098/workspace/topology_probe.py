"""Measure raw-grid diversity versus normalized relative topology.

Normalization removes translation and exact pair-color identity while retaining
wall positions and first-seen pair roles.  This is a shortcut-risk diagnostic,
not a label oracle or approval gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("reviewed_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def topology_signature(grid):
    occupied = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return ()
    min_r = min(r for r, _c, _v in occupied)
    min_c = min(c for _r, c, _v in occupied)
    order = []
    for row in grid:
        for value in row:
            if value not in (0, 8) and value not in order:
                order.append(value)
    role = {value: index + 1 for index, value in enumerate(order)}
    return tuple(
        sorted(
            (r - min_r, c - min_c, 8 if value == 8 else role[value])
            for r, c, value in occupied
        )
    )


def build_report(draws_per_band: int):
    if draws_per_band <= 0:
        raise ValueError("draws_per_band must be positive")
    generator = _load_generator()
    report = {
        "schema": "76e0bd03e098-topology-self-review-v1",
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "normalization": (
            "crop translation; relabel pair colors by first-seen order; retain wall positions"
        ),
        "sample_schedule": {
            "per_band": draws_per_band,
            "seed": "50000+i",
            "sample_index": "17*i+3",
        },
        "per_band": {},
        "overall": {},
    }
    all_topologies = set()
    all_inputs = set()
    all_shapes = set()
    total = 0
    for band in ("easy", "medium", "hard"):
        topologies = set()
        inputs = set()
        shapes = set()
        for index in range(draws_per_band):
            grid = generator.generate(50000 + index, 17 * index + 3, difficulty=band)
            topologies.add(topology_signature(grid))
            inputs.add(tuple(map(tuple, grid)))
            shapes.add((len(grid), len(grid[0])))
        report["per_band"][band] = {
            "draws": draws_per_band,
            "unique_inputs": len(inputs),
            "unique_shapes": len(shapes),
            "normalized_topologies": len(topologies),
        }
        all_topologies.update(topologies)
        all_inputs.update(inputs)
        all_shapes.update(shapes)
        total += draws_per_band
    report["overall"] = {
        "draws": total,
        "unique_inputs": len(all_inputs),
        "unique_shapes": len(all_shapes),
        "normalized_topologies": len(all_topologies),
        "assessment": (
            "Semantics are exhaustive but relative geometry is intentionally narrow; "
            "do not treat pixel uniqueness as topology breadth."
        ),
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=300)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.draws_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
