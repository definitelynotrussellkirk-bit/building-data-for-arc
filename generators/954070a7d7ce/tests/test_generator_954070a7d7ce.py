"""Independent structural regressions for the frame-local cross curriculum."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_frame_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def frame_boxes(grid):
    """Independent 4-neighbor color-9 component inventory, not gen's checker."""
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9}
    boxes = []
    while todo:
        stack = [todo.pop()]
        cells = set(stack)
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in todo:
                    todo.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                    if r in (r0, r1) or c in (c0, c1)}
        assert cells == expected, "nonrectangular or incomplete 9-frame"
        assert r1 - r0 >= 3 and c1 - c0 >= 3
        boxes.append((r0, c0, r1, c1))
    return sorted(boxes)


def independent_cross(grid):
    output = [row[:] for row in grid]
    used = set()
    for r0, c0, r1, c1 in frame_boxes(grid):
        top = [(c, grid[r0 + 1][c]) for c in range(c0 + 2, c1) if grid[r0 + 1][c]]
        left = [(r, grid[r][c0 + 1]) for r in range(r0 + 2, r1) if grid[r][c0 + 1]]
        assert len(top) == len(left) == 1
        (tc, color), (lr, other) = top[0], left[0]
        assert color == other and 1 <= color <= 8
        inside = {(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1) if grid[r][c]}
        assert inside == {(r0 + 1, tc), (lr, c0 + 1)}
        used |= inside
        for r in range(r0 + 1, r1):
            output[r][tc] = color
        for c in range(c0 + 1, c1):
            output[lr][c] = color
    assert used == {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
    return output


def example():
    grid = [[0] * 11 for _ in range(9)]
    for r in range(1, 8):
        for c in range(1, 9):
            if r in (1, 7) or c in (1, 8):
                grid[r][c] = 9
    grid[2][5] = grid[5][2] = 4
    return grid


def test_valid_frame():
    assert gen.self_check(example()) == []


@pytest.mark.parametrize("mutation", ["broken_wall", "mismatched", "extra_interior", "orphan9", "floating_mark", "no_frame"])
def test_structural_checker_rejects_invalid_scene(mutation):
    g = example()
    if mutation == "broken_wall":
        g[1][4] = 0
    elif mutation == "mismatched":
        g[5][2] = 7
    elif mutation == "extra_interior":
        g[4][4] = 3
    elif mutation == "orphan9":
        g[0][10] = 9
    elif mutation == "floating_mark":
        g[8][10] = 4
    else:
        g = [[9] * 11 for _ in range(9)]
        g[2][5] = g[5][2] = 4
    assert gen.self_check(g), mutation


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [["9"]], [[True]], [[-1]], [[10]]])
def test_checker_reports_malformed_grids_without_crashing(bad):
    assert gen.self_check(bad)


def test_degenerate_metadata_cannot_bypass_validation():
    assert gen.self_check([[0] * 11 for _ in range(9)], meta={"texture": "no_marks"})


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown|Unknown|unsupported"):
        gen.generate(0, 0, typo_axis=2)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(9, 11), (14, 20)])
def test_dimensions_are_valid_across_difficulties(band, shape):
    g = gen.generate(0, 0, difficulty=band, grid_h=shape[0], grid_w=shape[1])
    assert (len(g), len(g[0])) == shape
    assert gen.self_check(g) == []
    assert independent_cross(g) != g


@pytest.mark.parametrize("n_frames,n_colors", [(1, 1), (2, 1), (2, 2)])
def test_exact_frame_and_color_overrides(n_frames, n_colors):
    for seed in range(20):
        g = gen.generate(seed, 2, grid_h=9, grid_w=11, n_frames=n_frames, n_distinct_colors=n_colors)
        assert len(frame_boxes(g)) == n_frames
        palette = {v for row in g for v in row if v not in (0, 9)}
        assert len(palette) == n_colors
        assert independent_cross(g) != g


def test_impossible_combination_rejected_with_axis_names():
    with pytest.raises(ValueError, match="n_frames.*n_distinct_colors|n_distinct_colors.*n_frames"):
        gen.generate(0, 0, n_frames=1, n_distinct_colors=2)


@pytest.mark.parametrize("key,value", [("grid_h", 8), ("grid_h", 15), ("grid_w", 10), ("grid_w", 21), ("n_frames", 0), ("n_frames", 3), ("n_distinct_colors", 0), ("n_distinct_colors", 3), ("grid_h", True), ("grid_h", 10.5), ("grid_h", "11")])
def test_invalid_override_values_are_not_coerced(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_default_lessons_contain_shared_color_frames():
    for seed in range(12):
        for start in (0, 3, 7):
            cohort = [gen.generate(seed, i) for i in range(start, start + 4)]
            assert any(len(frame_boxes(g)) == 2 and len({v for row in g for v in row if v not in (0, 9)}) == 1 for g in cohort)


def test_default_geometry_is_not_locked_to_six_or_seven():
    boxes = [b for i in range(80) for b in frame_boxes(gen.generate(17, i))]
    assert any(b[3] - b[1] + 1 == 4 for b in boxes)
    assert any(b[3] - b[1] + 1 >= 8 for b in boxes)
    assert any(b[2] - b[0] + 1 != b[3] - b[1] + 1 for b in boxes)


def test_determinism_and_no_input_mutation():
    for seed in range(10):
        a = gen.generate(seed, 0)
        b = gen.generate(seed, 0)
        assert a == b and a is not b
        before = [row[:] for row in a]
        gen.self_check(a)
        assert a == before


def test_semantic_hooks_refute_color_global_shortcut():
    g = gen.generate(19, 0, n_frames=2, n_distinct_colors=1)
    expected = independent_cross(g)
    assert gen.rule_mirror(g) == expected
    assert gen.SEMANTIC_RIVALS["one_cross_per_color"](g) != expected
    assert gen.SEMANTIC_WITNESSES["shared_color_requires_frame_locality"](g)


def test_observer_reports_realized_values():
    g = gen.generate(19, 0, grid_h=10, grid_w=13, n_frames=2, n_distinct_colors=1)
    observed = gen.observe_overrides(g)
    assert observed == {"grid_h": 10, "grid_w": 13, "n_frames": 2, "n_distinct_colors": 1}


def test_mutation_fixtures_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    assert all(gen.self_check(g) for _, g in fixtures)


def test_default_four_demo_lessons_refute_declared_competitors():
    for seed in range(8):
        grids = [gen.generate(seed, i) for i in range(5)]
        demos = [{"input": g, "output": independent_cross(g)} for g in grids[:4]]
        assert gen.lesson_identifiable(demos, grids[4]) == []


def test_default_canvas_retains_canonical_scale_mass():
    # A distributional regression, not a replay of the battery's pinned seeds.
    # Larger canvases must remain reachable, but should not swamp the original
    # 9..12 by 11..15 teaching scale.
    grids = [gen.generate(seed, seed % 7, difficulty="hard") for seed in range(240)]
    in_envelope = sum(9 <= len(g) <= 12 and 11 <= len(g[0]) <= 15 for g in grids)
    assert in_envelope >= 0.60 * len(grids)
    assert any(len(g) > 12 or len(g[0]) > 15 for g in grids)
