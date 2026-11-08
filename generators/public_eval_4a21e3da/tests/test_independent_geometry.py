"""Literal geometric regressions authored independently before source review.

Expected labels below do not call the generator's Python solver. The task's
actual setting programs execute through the same-checkout protected Racket
runtime. Fixtures are portable and need no WORK/checks files or prior checkout.
"""

import importlib.util
from pathlib import Path
import sys

import pytest

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def _paint(h, w, orange, red, colors=(1, 7, 2)):
    background, foreground, marker = colors
    result = [[background] * w for _ in range(h)]
    for r, c in orange:
        result[r][c] = foreground
    for r, c in red:
        result[r][c] = marker
    return result


def _rotate(grid, turns):
    for _ in range(turns):
        grid = [list(row) for row in zip(*reversed(grid))]
    return grid


@pytest.fixture(scope="module")
def protected_apply():
    root = Path(__file__).resolve().parents[3]
    base = Path(__file__).resolve().parents[1] / "workspace/parametric"
    with _local_imports(root / "shared/runtime", base):
        spec = importlib.util.spec_from_file_location("_independent_geometry_adapter", base / "adapter.py")
        adapter = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = adapter
        spec.loader.exec_module(adapter)
        apply, identity, bridge = _real_evaluator(root / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield lambda mode, grid: _grid(apply(adapter.program({"selection": mode}), grid))
        finally:
            bridge.close()


CASES = [
    (
        "top_cut_preserves_disconnected_sector_geometry", "union", 9, 11,
        {(3,2),(3,3),(3,5),(3,7),(4,3),(4,5),(4,6),(4,7),(5,2),(5,4),(5,7),(6,5)},
        {(0,5)},
        {(0,0),(0,1),(1,1),(2,0),(2,2),(0,10),(1,9),(1,10),(2,10),(3,5),(4,5),(6,5)},
        {(0,5),(1,5),(2,5),(5,5)},
    ),
    (
        "bottom_axis_extent_differs_from_global_object_extent", "intersection", 11, 9,
        {(2,1),(3,1),(4,2),(5,2),(6,3),(7,1),(3,6),(4,6),(4,7),(5,5),(6,5),(7,6),(5,4),(7,4)},
        {(10,4)},
        {(5,0),(6,0),(7,1),(8,1),(9,2),(10,0),(6,7),(7,7),(7,8),(8,6),(9,6),(10,7),(5,4),(7,4)},
        {(6,4),(8,4),(9,4),(10,4)},
    ),
    (
        "union_moves_three_regions_and_deletes_opposite_region", "union", 11, 13,
        {(2,2),(2,3),(3,3),(4,4),(2,8),(3,8),(3,9),(4,10),(6,2),(7,2),(7,3),
         (6,8),(6,9),(7,9),(8,11),(2,6),(4,6),(7,6),(5,2),(5,5),(5,8),(5,10)},
        {(0,6),(5,12)},
        {(0,0),(0,1),(1,1),(2,2),(0,10),(1,10),(1,11),(2,12),(8,9),(8,10),(9,10),(10,12),
         (2,6),(4,6),(7,6),(5,2),(5,5),(5,8),(5,10)},
        {(0,6),(1,6),(3,6),(5,6),(6,6),(5,3),(5,4),(5,7),(5,9),(5,11),(5,12)},
    ),
    (
        "intersection_moves_only_jointly_incident_region", "intersection", 11, 13,
        {(2,2),(2,3),(3,3),(4,4),(2,8),(3,8),(3,9),(4,10),(6,2),(7,2),(7,3),
         (6,8),(6,9),(7,9),(8,11),(2,6),(4,6),(7,6),(5,2),(5,5),(5,8),(5,10)},
        {(0,6),(5,12)},
        {(0,10),(1,10),(1,11),(2,12),(2,6),(4,6),(7,6),(5,2),(5,5),(5,8),(5,10)},
        {(0,6),(1,6),(3,6),(5,6),(6,6),(5,3),(5,4),(5,7),(5,9),(5,11),(5,12)},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
@pytest.mark.parametrize("turns", range(4))
@pytest.mark.parametrize("colors", [(1, 7, 2), (9, 0, 3)])
def test_literal_geometry_in_all_orientations(protected_apply, case, turns, colors):
    _, mode, h, w, orange, red, expected_orange, expected_red = case
    inp = _rotate(_paint(h, w, orange, red, colors), turns)
    expected = _rotate(_paint(h, w, expected_orange, expected_red, colors), turns)
    assert protected_apply(mode, inp) == expected


@pytest.mark.parametrize("mode", ["union", "intersection"])
def test_meaningful_dense_30x30_uses_corner_background(protected_apply, mode):
    # 770 interior object cells; the background is deliberately not the mode.
    orange = {(r, c) for r in range(1, 29) for c in range(1, 29)
              if c != 14 or r % 2 == 0}
    inp = _paint(30, 30, orange, {(0, 14)}, (9, 0, 3))
    packed = {(r, c) for r in range(28) for c in (*range(13), *range(16, 30))}
    packed |= {(r, 14) for r in range(2, 29, 2)}
    rays = {(r, 14) for r in range(29) if r == 0 or r % 2 == 1}
    expected = _paint(30, 30, packed, rays, (9, 0, 3))
    assert len(orange) == 770
    assert protected_apply(mode, inp) == expected


@pytest.mark.parametrize("mode", ["union", "intersection"])
@pytest.mark.parametrize("two_axes", [False, True])
def test_no_off_axis_regions_is_a_total_case(protected_apply, mode, two_axes):
    if two_axes:
        inp = _paint(5, 5, {(2, 2)}, {(0, 2), (2, 4)})
        expected = _paint(5, 5, {(2, 2)}, {(0, 2), (1, 2), (2, 3), (2, 4)})
    else:
        inp = _paint(5, 5, {(1, 2), (3, 2)}, {(0, 2)})
        expected = _paint(5, 5, {(1, 2), (3, 2)}, {(0, 2), (2, 2)})
    assert protected_apply(mode, inp) == expected
