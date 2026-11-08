#!/usr/bin/env python3
"""Audit-only probe for cc9cb1d8bea8; writes evidence beside this file."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "cc9cb1d8bea8"
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
SOURCE = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_hash(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def call(gen, **kwargs):
    try:
        grid = gen.generate(19, 7, **kwargs)
    except Exception as exc:
        return {"status": "error", "type": type(exc).__name__, "message": str(exc)}
    return {
        "status": "ok",
        "grid_sha256": grid_hash(grid),
        "shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid),
        "colors": sorted({v for row in grid for v in row if v}),
    }


def main():
    gen = load_generator()
    canon = canonical_pairs(TASK, root=ROOT)
    canonical = []
    for index, pair in enumerate(canon):
        canonical.append({
            "pair": index,
            "input_shape": [len(pair["input"]), len(pair["input"][0])],
            "output_shape": [len(pair["output"]), len(pair["output"][0])],
            "self_check": gen.self_check(pair["input"]),
        })

    cases = {
        "baseline": call(gen),
        "easy_grid_h_10_declared_valid": call(gen, difficulty="easy", grid_h=10),
        "n_components_5_declared_valid": call(gen, n_components=5),
        "unknown_key": call(gen, not_a_declared_axis=123),
    }
    for axis, values in {
        "palette_kind": ["default", "warm", "cool", "varied"],
        "palette_size": [3, 4, 5],
        "n_distinct_colors": [3, 4, 5],
        "position_bias": ["k_t1_t2_plus_components"],
        "density": ["sparse"],
        "texture": ["default", "warm", "cool", "varied", "tied_sizes", "no_k", "identity_transforms"],
    }.items():
        for value in values:
            cases[f"{axis}={value}"] = call(gen, **{axis: value})

    baseline_hash = cases["baseline"].get("grid_sha256")
    same_as_baseline = {
        key: (value.get("grid_sha256") == baseline_hash)
        for key, value in cases.items()
        if value.get("status") == "ok"
    }
    result = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "canonical_pair_count": len(canon),
        "canonical_rejected": sum(bool(item["self_check"]) for item in canonical),
        "canonical": canonical,
        "cases": cases,
        "same_as_baseline": same_as_baseline,
        "scope": "Fixed seed=19, sample_index=7 override probes plus all five canonical pairs.",
    }
    (HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "canonical-inputs.json").write_text(
        json.dumps([pair["input"] for pair in canon], indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
