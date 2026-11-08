#!/usr/bin/env python3
"""Reproduce the multi-rival curriculum counterexample for 056999828b88."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO = TASK_DIR.parents[1]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

DEFAULT_REQUEST = {
    "seed": 918273,
    "sample_index": 3,
    "difficulty": "easy",
    "overrides": {"grid_h": 8, "grid_w": 10, "n_objects": 3},
}


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("counterexample_056999828b88", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _component_row(generator, obj) -> dict[str, Any]:
    piece = generator._crop_piece(obj)
    shape_key = generator._shape_key(obj["cells"])
    return {
        "color": obj["color"],
        "size": len(obj["cells"]),
        "height": piece["h"],
        "width": piece["w"],
        "bbox_area": piece["h"] * piece["w"],
        "bbox_semiperimeter": piece["h"] + piece["w"],
        "boundary_perimeter": generator._boundary_perimeter(piece),
        "adjacency_edges": generator._adjacency_edges(piece),
        "boundary_cells": generator._boundary_cells(piece),
        "max_span": max(piece["h"], piece["w"]),
        "min_span": min(piece["h"], piece["w"]),
        "shape_key": [list(cell) for cell in shape_key],
        "legacy_shape": shape_key in generator._LEGACY_SHAPE_KEYS,
    }


def build_report(generator, generator_path: Path, request: dict[str, Any] | None = None):
    request = dict(DEFAULT_REQUEST if request is None else request)
    request["overrides"] = dict(request.get("overrides", {}))
    grid = generator.generate(
        request["seed"],
        request["sample_index"],
        difficulty=request.get("difficulty"),
        **request["overrides"],
    )
    intended = generator._size_pack(grid)
    outputs = {
        name: shortcut(grid)
        for name, shortcut in generator.CANONICAL_SHORTCUTS.items()
    }
    disagreements = {
        name: output != intended for name, output in outputs.items()
    }
    offset = {"easy": 0, "medium": 1, "hard": 2}.get(request.get("difficulty"), 1)
    companion_request = dict(request, sample_index=(2-offset) % 4)
    companion = generator.generate(companion_request["seed"], companion_request["sample_index"],
        difficulty=companion_request.get("difficulty"), **companion_request["overrides"])
    companion_truth = generator._size_pack(companion)
    companion_outputs = {name: shortcut(companion) for name, shortcut in generator.CANONICAL_SHORTCUTS.items()}
    across_cases = {name: disagreements[name] or companion_outputs[name] != companion_truth for name in outputs}
    return {
        "schema": "056999828b88-shortcut-counterexample/3",
        "all_shortcuts_refuted_across_cases": all(across_cases.values()),
        "companion_case": {"request": companion_request, "input": companion,
            "intended_output": companion_truth, "shortcut_outputs": companion_outputs,
            "self_check": generator.self_check(companion)},
        "generator_sha256": hashlib.sha256(Path(generator_path).read_bytes()).hexdigest(),
        "request": request,
        "input": grid,
        "components": [
            _component_row(generator, obj) for obj in generator._components(grid)
        ],
        "intended_size_order_output": intended,
        "shortcut_outputs": outputs,
        "shortcut_disagreements": disagreements,
        "all_declared_shortcuts_disagree": bool(disagreements)
        and all(disagreements.values()),
        "self_check": generator.self_check(
            grid, difficulty=request.get("difficulty")
        ),
        "firing_witnesses": sorted(
            name
            for name, witness in generator.SEMANTIC_WITNESSES.items()
            if witness(grid)
        ),
    }


def main() -> int:
    generator, path = load_generator()
    report = build_report(generator, path)
    out = WORKSPACE / "shortcut_counterexample.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_shortcuts_refuted_across_cases"] and not report["self_check"] and not report["companion_case"]["self_check"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
