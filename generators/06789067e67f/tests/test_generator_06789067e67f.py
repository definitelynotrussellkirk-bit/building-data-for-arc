from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "06789067e67f"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"


def _load():
    spec = importlib.util.spec_from_file_location("generator_06789067e67f_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load()


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def _key(grid, component):
    color, cells = component
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    body = {(r - r0, c - c0) for r, c in cells}
    height, width = r1 - r0 + 1, c1 - c0 + 1
    seen = set()
    holes = 0
    for r in range(height):
        for c in range(width):
            if (r, c) in body or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            touches = False
            while stack:
                rr, cc = stack.pop()
                touches |= rr in (0, height - 1) or cc in (0, width - 1)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in body and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches:
                holes += 1
    return holes, len(cells), color


def test_contract_is_pinned_and_excludes_contradictory_single_component(gen):
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "82b12cea1db8"
    assert "single_component" not in gen.AXES["texture"]["valid"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(10, 12), (18, 22)])
def test_advertised_size_endpoints_and_component_counts_are_realizable(gen, difficulty, height, width):
    grid = gen.generate(
        20261026,
        height * 100 + width,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        n_comps=4,
        texture="plain",
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(_components(grid)) == 4
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("texture", ["plain", "tie_holes", "tie_area", "all_solid"])
def test_all_declared_textures_generate_valid_deterministic_scenes(gen, texture):
    kwargs = dict(difficulty="medium", grid_h=14, grid_w=17, n_comps=4, texture=texture)
    first = gen.generate(17, 3, **kwargs)
    second = gen.generate(17, 3, **kwargs)
    assert first == second
    assert gen.self_check(first) == []
    keys = [_key(first, comp) for comp in _components(first)]
    assert len(keys) == 4
    if texture == "tie_holes":
        assert any(a[0] == b[0] and a[1] != b[1] for i, a in enumerate(keys) for b in keys[i + 1 :])
    if texture == "tie_area":
        assert any(a[:2] == b[:2] and a[2] != b[2] for i, a in enumerate(keys) for b in keys[i + 1 :])
    if texture == "all_solid":
        assert {row[0] for row in keys} == {0}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"texture": "not_a_declared_texture"},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"n_comps": "3"},
        {"grid_h": 9},
        {"grid_w": 23},
        {"n_comps": 1},
    ],
)
def test_invalid_controls_fail_closed(gen, kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_self_check_rejects_malformed_and_single_component_grids(gen):
    assert gen.self_check([[True]])
    assert gen.self_check([[1, 1], [1, 1]])
    assert gen.self_check([[1, 0], [0]])
