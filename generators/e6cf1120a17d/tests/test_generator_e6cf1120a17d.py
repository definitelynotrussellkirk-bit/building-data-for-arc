"""Base-source regressions for e6cf1120a17d."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_generator_e6cf1120a17d", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_summary_matches_canonical_interior_clear():
    generator = _load_generator()
    lowered = generator.SUMMARY.lower()
    assert "clear" in lowered
    assert "background 0" in lowered
    assert "restoring the solid rect" not in lowered


def test_explicit_boundary_input_is_lawful():
    generator = _load_generator()
    grid = generator.generate(
        7,
        0,
        difficulty=None,
        grid_h=30,
        grid_w=30,
        rect_h=28,
        rect_w=28,
        rect_rr=1,
        rect_rc=1,
        rect_color=5,
        corner_colors=[1, 2, 3, 4],
    )
    assert [len(grid), len(grid[0])] == [30, 30]
    assert generator.self_check(grid) == []
