from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
GENERATOR = HOME / "generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return _load(GENERATOR, "_test_generator_067f6e037e97")


def _same_color_component_sizes(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    sizes: list[int] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            size = 0
            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(size)
    return sizes


def _int_bounds(axis: dict[str, str]) -> tuple[int, int]:
    low, high = axis["valid"].split("..")
    return int(low), int(high)


def test_advertised_integer_axis_boundaries_are_real_overrides(base):
    """Catches AXES values that are advertised but rejected by generate()."""
    defaults = {"texture": "plain"}
    for name in ("grid_h", "grid_w", "seed_count"):
        low, high = _int_bounds(base.AXES[name])
        for value in (low, high):
            grid = base.generate(991, 3, **defaults, **{name: value})
            assert base.self_check(grid) == []
            if name == "grid_h":
                assert len(grid) == value
            elif name == "grid_w":
                assert len(grid[0]) == value
            else:
                assert sum(cell != 0 for row in grid for cell in row) == value


def test_any_three_consecutive_default_examples_refute_one_stamp_per_object(base):
    """Catches a lesson schedule where all three examples contain only isolated seeds."""
    for start in range(12):
        grids = [base.generate(0, start + offset, difficulty="medium") for offset in range(3)]
        assert any(max(_same_color_component_sizes(grid), default=0) >= 2 for grid in grids)


def test_blob_texture_honors_exact_seed_count_override(base):
    """Catches blob construction silently inflating seed_count=1 to two cells."""
    for count in (1, 2, 6):
        grid = base.generate(991, 3, texture="blob", seed_count=count)
        assert sum(cell != 0 for row in grid for cell in row) == count
        if count >= 2:
            assert max(_same_color_component_sizes(grid), default=0) >= 2


def test_full_grid_degenerate_always_changes_color_eight_output(base):
    """Catches full_grid occasionally drawing color 8 and becoming an identity case."""
    for seed in range(32):
        grid = base.generate(seed, 0, texture="full_grid")
        colors = {cell for row in grid for cell in row}
        assert len(colors) == 1
        assert 8 not in colors
