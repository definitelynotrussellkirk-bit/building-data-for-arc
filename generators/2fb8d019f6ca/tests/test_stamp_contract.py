"""Behavioral regressions for rooted extraction and exact, disjoint stamping."""
from copy import deepcopy
from itertools import product

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("2fb8d019f6ca", root=ROOT)


def rooted_cells(grid):
    cells = set()
    pending = [(0, 0)]
    while pending:
        r, c = pending.pop()
        if (r, c) in cells or not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            continue
        if grid[r][c] in (0, 8):
            continue
        cells.add((r, c))
        pending.extend(((r-1, c), (r+1, c), (r, c-1), (r, c+1)))
    return cells


def independent_stamp(grid):
    """Test oracle, separately checked against canonical and live Racket labels."""
    out = [[0] * len(grid[0]) for _ in grid]
    root = rooted_cells(grid)
    for ar, row in enumerate(grid):
        for ac, value in enumerate(row):
            if value == 8:
                for r, c in root:
                    if ar+r < len(grid) and ac+c < len(grid[0]):
                        out[ar+r][ac+c] = grid[r][c]
    return out


def assert_disjoint(grid):
    root = rooted_cells(grid)
    h, w = max(r for r, _ in root)+1, max(c for _, c in root)+1
    occupied = {(r, c) for r in range(h) for c in range(w)}
    for ar, row in enumerate(grid):
        for ac, value in enumerate(row):
            if value != 8:
                continue
            assert ar+h <= len(grid) and ac+w <= len(grid[0])
            box = {(ar+r, ac+c) for r in range(h) for c in range(w)}
            assert not box & occupied, (ar, ac, sorted(box & occupied))
            occupied.update(box)


def test_legacy_overlap_witness_is_rejected():
    grid = [[0] * 10 for _ in range(8)]
    grid[0][:2] = [2, 3]
    grid[1][:2] = [3, 2]
    grid[3][3] = grid[3][4] = 8
    assert GEN.self_check(grid), "validator accepted intersecting stamp footprints"


def test_requested_palette_is_realized_and_alias_is_not_a_second_axis():
    grid = GEN.generate(7, 19, difficulty="medium", palette_size=4, n_distinct_colors=4)
    assert len({v for row in grid for v in row} - {0}) == 4
    assert "n_distinct_colors" not in GEN.AXES
    with pytest.raises(ValueError):
        GEN.generate(7, 19, palette_size=2, n_distinct_colors=4)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_joint_boundary_controls_are_exact_and_collision_free(band):
    for index, values in enumerate(product((8, 16), (10, 16), (1, 4), (2, 4), (3, 8), (0, 1))):
        request = dict(zip(("grid_h", "grid_w", "n_anchors", "palette_size", "template_cells", "n_distractors"), values))
        grid = GEN.generate(19, index, difficulty=band, **request)
        assert not GEN.self_check(grid), (request, GEN.self_check(grid))
        root = rooted_cells(grid)
        observed = {
            "grid_h": len(grid), "grid_w": len(grid[0]),
            "n_anchors": sum(v == 8 for row in grid for v in row),
            "palette_size": len({v for row in grid for v in row} - {0}),
            "template_cells": len(root),
            "n_distractors": sum(v not in (0, 8) and (r, c) not in root
                                 for r, row in enumerate(grid) for c, v in enumerate(row)),
        }
        assert observed == request
        assert GEN.observe_overrides(grid) == request
        assert_disjoint(grid)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "n_anchors", "palette_size", "template_cells", "n_distractors", "n_distinct_colors"])
@pytest.mark.parametrize("value", [True, 3.0, "3", -1])
def test_invalid_scalar_overrides_are_rejected(axis, value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(1, 1, **{axis: value})


def test_unknown_and_retired_controls_fail_explicitly():
    for axis in ("typo", "palette_kind", "texture", "density", "position_bias"):
        with pytest.raises(ValueError):
            GEN.generate(1, 1, **{axis: "warm"})


@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "__invalid_difficulty__"),
])
def test_invalid_call_arguments_are_rejected(argument, value):
    arguments = {"seed": 7, "sample_index": 1, "difficulty": "medium"}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**arguments)


def test_canonical_examples_remain_valid_and_all_claimed_shortcuts_fit():
    pairs = canonical_pairs("2fb8d019f6ca", root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_stamp(pair["input"]) == pair["output"]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_broad_draw_refutes_each_declared_shortcut(band):
    for seed in range(12):
        for index in range(12):
            grid = GEN.generate(seed, index, difficulty=band)
            assert GEN.generate(seed, index, difficulty=band) == grid
            assert GEN.self_check(grid) == []
            assert_disjoint(grid)
            if index % 2:
                assert GEN.schedule_profile(seed, index, band) == "extraction_witness"
                expected = independent_stamp(grid)
                before = deepcopy(grid)
                for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                    assert rival(grid) != expected, (seed, index, name)
                    assert grid == before, name


@pytest.mark.parametrize("bad", [[], [[]], [[2], [0, 8]], [[True, 8]], [[2.5, 8]], [[11, 8]], [[0, 8]]])
def test_validator_rejects_malformed_or_rootless_grids(bad):
    assert GEN.self_check(bad)
