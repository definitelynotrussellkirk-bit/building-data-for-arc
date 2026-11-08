#!/usr/bin/env python3
"""Reproduce and guard the exact contact-topology contract for task 5a85abd1e231.

Run from any working directory.  The probe checks one lawful separated sample,
one lawful one-cell touching sample, and the historical false acceptance: two
3x3 tiles joined along a two-cell seam.  It exits nonzero if the generator's
self-check stops distinguishing those manifolds.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


TASK_ID = "5a85abd1e231"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"


def load_generator() -> ModuleType:
    sys.path.insert(0, str(RUNTIME_ROOT))
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"contact_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def two_cell_seam_grid(gen: ModuleType) -> list[list[int]]:
    """Build the minimal known off-manifold layout accepted before v4.1.0."""
    origins = [
        (0, 0),
        (3, 1),  # two cardinal contacts with the tile at (0, 0)
        (9, 6),
        (12, 1),
        (7, 10),
        (2, 6),
        (11, 12),
        (3, 12),
        (13, 8),
    ]
    colors = [1, 2, 3, 4, 6, 7, 8, 1]
    grid = [[0 for _ in range(15)] for _ in range(16)]
    for origin, direction, color in zip(origins[:8], gen._DIRECTION_ORDER, colors):
        gen._stamp_tile(grid, origin[0], origin[1], direction, color)
    gen._stamp_tile(grid, origins[8][0], origins[8][1], None, None)
    return grid


def summarize(gen: ModuleType, grid: list[list[int]]) -> dict[str, Any]:
    analysis = gen._analysis(grid)
    return {
        "components": analysis.get("components"),
        "contact_sizes": analysis.get("contact_sizes"),
        "contact_mode": analysis.get("contact_mode"),
        "errors": gen.self_check(grid),
    }


def main() -> int:
    gen = load_generator()
    separated = gen.generate(
        20261003,
        0,
        difficulty="easy",
        scene_profile="16x15_palette9",
        contact_mode="separated",
    )
    lawful_touch = gen.generate(
        20261003,
        1,
        difficulty="easy",
        scene_profile="16x15_palette9",
        contact_mode="touching_pair",
    )
    unlawful_touch = two_cell_seam_grid(gen)

    report = {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "separated": summarize(gen, separated),
        "lawful_one_cell_touch": summarize(gen, lawful_touch),
        "unlawful_two_cell_seam": summarize(gen, unlawful_touch),
    }

    assert report["separated"]["errors"] == []
    assert report["separated"]["contact_sizes"] == []
    assert report["lawful_one_cell_touch"]["errors"] == []
    assert report["lawful_one_cell_touch"]["contact_sizes"] == [1]
    assert report["unlawful_two_cell_seam"]["contact_sizes"] == [2]
    assert report["unlawful_two_cell_seam"]["contact_mode"] is None
    assert any(
        "exactly one cardinal edge cell" in error
        for error in report["unlawful_two_cell_seam"]["errors"]
    )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
