from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "01023c69fe3c"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("_generator_01023c69fe3c", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_near_corners_small_grid_never_collapses_anchor_rows_or_columns():
    generator = _load_generator()
    for seed in range(32):
        grid = generator.generate(
            seed,
            0,
            difficulty="easy",
            grid_h=5,
            grid_w=6,
            texture="near_corners",
            edge_avoidance=True,
            n_decor=0,
        )
        assert generator.self_check(grid) == []


def test_generator_pins_current_canonical_rule_hash():
    generator = _load_generator()
    assert generator.RULE_HASH == "a403765e8e23"


def test_n_decor_accepts_declared_upper_bound():
    generator = _load_generator()
    grid = generator.generate(
        7,
        0,
        difficulty="hard",
        grid_h=18,
        grid_w=20,
        dot_orientation="spread",
        dot_separation="far",
        edge_avoidance=True,
        n_decor=6,
    )
    assert generator.self_check(grid) == []
    assert sum(value not in (0, 2) for row in grid for value in row) == 6
