"""Portable literal fixtures independent of the candidate Python labeler."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def rotate(grid, turns=1):
    for _ in range(turns):
        grid = [list(row) for row in zip(*reversed(grid))]
    return grid


def panel(grid, origin, wall, direction, tail=1):
    if direction == "southeast":
        patch = [[wall] * 7 for _ in range(6)]
        tails = ((1, 3), (2, 1), (2, 4), (3, 2))
        heads = ((3, 5), (4, 3))
    else:
        patch = [[wall] * 5 for _ in range(5)]
        tails = ((1, 1), (1, 2), (3, 1), (3, 2))
        heads = ((1, 3), (3, 3))
    for r, c in tails:
        patch[r][c] = tail
    for r, c in heads:
        patch[r][c] = 2
    if direction == "south":
        patch = rotate(patch)
    r0, c0 = origin
    for r, row in enumerate(patch):
        for c, value in enumerate(row):
            grid[r0 + r][c0 + c] = value


def enclosure(grid, bounds, wall):
    r0, c0, r1, c1 = bounds
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                grid[r][c] = wall


def put_tokens(grid, positions):
    result = deepcopy(grid)
    for r, c in positions:
        assert result[r][c] == 0
        result[r][c] = 4
    return result


@pytest.fixture(scope="module")
def protected_apply():
    root = Path(__file__).resolve().parents[3]
    base = Path(__file__).resolve().parents[1] / "workspace/parametric"
    with _local_imports(root / "shared/runtime", base):
        spec = importlib.util.spec_from_file_location("_independent_motion_adapter", base / "adapter.py")
        adapter = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = adapter
        spec.loader.exec_module(adapter)
        apply, identity, bridge = _real_evaluator(root / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield lambda mode, grid: _grid(apply(adapter.program({"motion": mode}), grid))
        finally:
            bridge.close()


def literal_cases():
    grid = [[0] * 18 for _ in range(12)]
    panel(grid, (0, 0), 5, "east")
    enclosure(grid, (2, 7, 10, 16), 5)
    yield ("long_slide_and_stationary_token", grid, [(3, 8), (7, 15)],
           {"toward_head": [(3, 15), (7, 15)], "toward_tail": [(3, 8), (7, 8)]})

    grid = [[0] * 26 for _ in range(20)]
    panel(grid, (0, 18), 5, "east", tail=7)
    panel(grid, (0, 1), 7, "south")
    enclosure(grid, (7, 1, 17, 11), 5)
    enclosure(grid, (7, 14, 17, 24), 7)
    yield ("enclosure_color_beats_nearest_panel", grid, [(9, 4), (13, 8), (9, 17), (12, 21)],
           {"toward_head": [(9, 10), (13, 10), (16, 17), (16, 21)],
            "toward_tail": [(9, 2), (13, 2), (8, 17), (8, 21)]})

    grid = [[0] * 22 for _ in range(18)]
    panel(grid, (0, 0), 6, "southeast")
    enclosure(grid, (2, 10, 16, 20), 6)
    for r in range(2, 8):
        grid[r][15] = 6
    yield ("forward_side_wall_blocks_diagonal_but_other_tokens_do_not", grid,
           [(5, 12), (6, 12), (11, 13)],
           {"toward_head": [(7, 14), (13, 19), (15, 17)],
            "toward_tail": [(4, 11), (5, 11), (9, 11)]})


CASES = list(literal_cases())


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
@pytest.mark.parametrize("turns", range(4))
@pytest.mark.parametrize("mode", ["toward_head", "toward_tail"])
def test_literal_motion_geometry(protected_apply, case, turns, mode):
    _, grid, origins, destinations = case
    inp = rotate(put_tokens(grid, origins), turns)
    expected = rotate(put_tokens(grid, destinations[mode]), turns)
    assert protected_apply(mode, inp) == expected


@pytest.mark.parametrize("mode", ["toward_head", "toward_tail"])
def test_30x30_many_independent_rays_have_literal_endpoints(protected_apply, mode):
    grid = [[0] * 30 for _ in range(30)]
    panel(grid, (0, 0), 3, "east")
    enclosure(grid, (1, 8, 28, 28), 3)
    origins = [(r, 10 + (r * 7) % 15) for r in range(2, 28)]
    endpoint_column = 27 if mode == "toward_head" else 9
    expected = put_tokens(grid, [(r, endpoint_column) for r in range(2, 28)])
    assert protected_apply(mode, put_tokens(grid, origins)) == expected


@pytest.mark.parametrize("mode", ["toward_head", "toward_tail"])
def test_one_cell_chamber_is_total_and_stationary(protected_apply, mode):
    grid = [[0] * 10 for _ in range(10)]
    panel(grid, (0, 0), 7, "east")
    enclosure(grid, (6, 6, 8, 8), 7)
    inp = put_tokens(grid, [(7, 7)])
    assert protected_apply(mode, inp) == inp
