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
    return _load(GENERATOR, "_test_generator_7358813cf026")


def _int_bounds(axis: dict[str, str]) -> tuple[int, int]:
    low, high = axis["valid"].split("..")
    return int(low), int(high)


def _same_color_objects(grid: list[list[int]]) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, int]] = []
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
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, size))
    return result


def test_axes_only_advertise_consumed_real_domains(base):
    """Catches metadata-only knobs and integer endpoints rejected by generate()."""
    assert set(base.AXES) == {"grid_h", "grid_w", "singletons", "palette_kind", "texture"}
    for name in ("grid_h", "grid_w", "singletons"):
        low, high = _int_bounds(base.AXES[name])
        for value in (low, high):
            grid = base.generate(7991902016299830411, 2098244023, **{name: value})
            assert base.self_check(grid) == []
            if name == "grid_h":
                assert len(grid) == value
            elif name == "grid_w":
                assert len(grid[0]) == value
            else:
                assert sum(size == 1 for _, size in _same_color_objects(grid)) == value


def test_self_check_matches_same_color_object_semantics(base):
    """Catches treating adjacent different colors as one canonical object."""
    grid = [
        [3, 4, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 5, 5],
    ]
    assert base.self_check(grid) == []


def test_components_touching_degenerate_is_one_same_color_object(base):
    """Catches a degenerate fixture whose comment disagrees with Racket objects(g,0)."""
    grid = base._draw_from_degenerate("components_touching", None)
    assert sorted(size for _, size in _same_color_objects(grid)) == [2]


def test_palette_kind_is_a_real_generation_control(base):
    """Catches a declared palette knob that is accepted but ignored."""
    grid = base.generate(23, 4, palette_kind="warm")
    colors = {cell for row in grid for cell in row if cell}
    assert colors
    assert colors <= set(base.PALETTES["warm"])


@pytest.mark.parametrize("texture", ("no_singletons", "all_singletons", "components_touching"))
def test_degenerate_textures_honor_reserved_grid_dimensions(base, texture):
    """Catches texture branches that accept grid_h/grid_w but return a fixed 9x10 canvas."""
    for h, w in ((8, 8), (11, 12)):
        grid = base.generate(23, 4, texture=texture, grid_h=h, grid_w=w)
        assert (len(grid), len(grid[0])) == (h, w)
