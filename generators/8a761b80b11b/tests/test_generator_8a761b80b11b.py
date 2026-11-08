"""Base-source regressions for 8a761b80b11b."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_generator_8a761b80b11b", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runs(grid):
    found = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            start, color = c, row[c]
            while c < len(row) and row[c] == color:
                c += 1
            found.append((r, start, c - 1, color))
    return found


def test_unknown_and_stale_controls_are_rejected():
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, mystery=1)
    for stale in ("palette_size", "position_bias", "n_distinct_colors", "density"):
        with pytest.raises(ValueError, match="unknown override"):
            generator.generate(0, 0, **{stale: 1})


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_explicit_dimensions_are_valid_across_difficulty_bands(difficulty):
    generator = _load_generator()
    grid = generator.generate(
        4, 1, difficulty=difficulty,
        grid_h=12, grid_w=18, n_runs=12, palette_kind="cool",
    )
    assert [len(grid), len(grid[0])] == [12, 18]
    runs = _runs(grid)
    assert len(runs) == 12
    assert max(end - start + 1 for _, start, end, _ in runs) >= 3
    assert {color for *_, color in runs} <= set(generator.PALETTES["cool"])
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_draws_have_exact_run_count_and_observable_reduction(difficulty):
    generator = _load_generator()
    for seed in range(8):
        grid = generator.generate(seed, 2, difficulty=difficulty)
        runs = _runs(grid)
        assert len(runs) >= 1
        assert any(end - start + 1 >= 3 for _, start, end, _ in runs)
        assert generator.self_check(grid) == []


@pytest.mark.parametrize("texture", ["no_runs", "vertical_only", "all_singletons"])
def test_degenerate_textures_honor_explicit_dimensions(texture):
    generator = _load_generator()
    grid = generator.generate(5, 0, grid_h=9, grid_w=13, texture=texture)
    assert [len(grid), len(grid[0])] == [9, 13]
    if texture == "no_runs":
        assert not any(any(row) for row in grid)
    elif texture == "vertical_only":
        assert any(grid[r][c] and grid[r + 1][c] == grid[r][c] for r in range(8) for c in range(13))
        assert all(end == start for _, start, end, _ in _runs(grid))
    else:
        assert all(end == start for _, start, end, _ in _runs(grid))


def test_conflicting_texture_alias_and_palette_kind_is_rejected():
    generator = _load_generator()
    with pytest.raises(ValueError, match="conflict"):
        generator.generate(0, 0, texture="warm", palette_kind="cool")
