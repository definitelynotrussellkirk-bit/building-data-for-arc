"""Focused regressions for the selected dbecc530afd0 generator."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "dbecc530afd0"
ROOT = find_root(Path(__file__))
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _blank(h: int = 18, w: int = 18) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _put_rect(grid: list[list[int]], r1: int, r2: int, c1: int, c2: int) -> None:
    for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
        grid[r][c] = 4


def three_rectangle_counterexample() -> list[list[int]]:
    grid = _blank()
    _put_rect(grid, 1, 3, 1, 3)
    _put_rect(grid, 7, 9, 7, 9)
    _put_rect(grid, 13, 15, 13, 15)
    return grid


def interleaved_counterexample() -> list[list[int]]:
    """Two lawful rectangles whose yellow-bearing row intervals interleave."""
    grid = _blank(10, 11)
    _put_rect(grid, 1, 5, 1, 4)
    _put_rect(grid, 3, 7, 6, 9)
    return grid


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _changed_cells(before: list[list[int]], after: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, (row_before, row_after) in enumerate(zip(before, after))
        for c, (a, b) in enumerate(zip(row_before, row_after))
        if a != b
    }


def test_rejects_retained_three_rectangle_audit_counterexample():
    grid = three_rectangle_counterexample()
    assert gen.observe_overrides(grid)["n_rects"] == 3
    assert any("1..2" in error or "one or two" in error for error in gen.self_check(grid))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": True},
        {"grid_h": 8.0},
        {"grid_h": "8"},
        {"grid_h": 7},
        {"grid_w": 19},
        {"n_rects": 0},
        {"n_rects": 3},
        {"n_extra_yellows": -1},
        {"n_extra_yellows": 4},
        {"position_bias": 3},
        {"position_bias": "unknown"},
        {"texture": 3},
        {"texture": "no_rect"},
        {"texture": "three_yellows"},
        {"texture": "full_grid"},
    ],
)
def test_rejects_invalid_overrides(kwargs):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (0.0, 0, None),
        ("0", 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0.0, None),
        (0, 0, "expert"),
        (0, 0, 2),
    ],
)
def test_rejects_invalid_request_scalars(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize(
    "grid",
    [
        [[4 if (r, c) in {(2, 2), (5, 7)} else 0 for c in range(12)] for r in range(12)],
        [[4 if (r, c) in {(2, 2), (2, 8), (8, 2)} else 0 for c in range(12)] for r in range(12)],
        [[4 for _ in range(12)] for _ in range(12)],
    ],
    ids=["two_yellows", "three_yellows", "full_grid"],
)
def test_former_diagnostic_layouts_are_not_lawful(grid):
    assert gen.self_check(grid)


def test_rejects_shared_corner_rectangles_and_too_many_isolated_yellows():
    shared = _blank(10, 10)
    # Two complete rectangles share the left vertical side.
    for point in {(1, 1), (1, 4), (5, 1), (5, 4), (1, 7), (5, 7)}:
        shared[point[0]][point[1]] = 4
    assert gen.self_check(shared)

    extras = _blank(10, 10)
    _put_rect(extras, 1, 5, 1, 5)
    for point in ((0, 9), (2, 8), (7, 0), (9, 7)):
        extras[point[0]][point[1]] = 4
    assert len(gen._all_rects({(r, c) for r, row in enumerate(extras) for c, v in enumerate(row) if v == 4})) == 1
    assert gen.self_check(extras)


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_accepts_canonical_and_python_mirror_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen._intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_declared_adjacent_row_shortcut_fits_every_canonical_pair(pair):
    assert gen._adjacent_equal_row_pairs_only(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_bypass_schedule_and_are_observable(band):
    kwargs = {
        "grid_h": 18,
        "grid_w": 18,
        "n_rects": 2,
        "n_extra_yellows": 3,
        "position_bias": "scattered",
        "texture": "scattered",
    }
    grid = gen.generate(901, 0, difficulty=band, **kwargs)
    assert gen.self_check(grid) == []
    assert (len(grid), len(grid[0])) == (18, 18)
    assert gen.observe_overrides(grid) == {"n_rects": 2, "n_extra_yellows": 3}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_slot_schedule_has_ten_canonical_and_ten_interleaved_draws_per_twenty(band):
    profiles = []
    for sample_index in range(20):
        grid = gen.generate(8127, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(8127, sample_index, difficulty=band)
        profiles.append(gen.schedule_profile(8127, sample_index, band))
        if sample_index % 2 == 0:
            assert _profile(grid) == (10, 10, 2)
        else:
            assert gen._has_interleaved_rectangles(grid)
            assert gen._adjacent_equal_row_pairs_only(grid) != gen._intended_output(grid)
    assert profiles == [gen.SCHEDULE_PROFILES[i % 4] for i in range(20)]
    assert sum(_profile(gen.generate(8127, i, difficulty=band)) == (10, 10, 2) for i in range(20)) == 10



def test_sample_index_zero_anchor_varies_across_seeds_without_becoming_a_witness():
    """Mutation caught: collapsing default seed diversity to the four official grids."""
    grids = [gen.generate(seed, 0) for seed in range(40)]
    signatures = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(signatures) >= 5
    for grid in grids:
        assert _profile(grid) == (10, 10, 2)
        assert gen.self_check(grid) == []
        assert gen._adjacent_equal_row_pairs_only(grid) == gen._intended_output(grid)

def test_interleaved_counterexample_is_lawful_and_exactly_disagrees_with_shortcut():
    grid = interleaved_counterexample()
    assert gen.self_check(grid) == []
    assert gen._has_interleaved_rectangles(grid)
    intended = gen._intended_output(grid)
    rival = gen._adjacent_equal_row_pairs_only(grid)
    assert rival == grid
    assert intended != rival
    assert _changed_cells(grid, intended) == (
        {(r, c) for r in range(2, 5) for c in range(2, 4)}
        | {(r, c) for r in range(4, 7) for c in range(7, 9)}
    )


def test_every_query_rotation_of_scheduled_window_retains_rival_refutation():
    inputs = [gen.generate(551, i, difficulty="medium") for i in range(4)]
    pairs = [{"input": grid, "output": gen._intended_output(grid)} for grid in inputs]
    assert sum(gen._has_interleaved_rectangles(pair["input"]) for pair in pairs) == 2
    for query_index in range(4):
        demos = [deepcopy(pair) for index, pair in enumerate(pairs) if index != query_index]
        query = deepcopy(pairs[query_index])
        assert any(
            gen._adjacent_equal_row_pairs_only(demo["input"]) != demo["output"]
            for demo in demos
        )
        assert gen.lesson_identifiable(demos, query) == []


def test_semantic_declarations_bind_witness_to_same_named_rival():
    rival_name = "adjacent_equal_row_pairs_only"
    assert gen.SEMANTIC_RIVALS[rival_name] is gen._adjacent_equal_row_pairs_only
    assert gen.CANONICAL_SHORTCUTS[rival_name] is gen._adjacent_equal_row_pairs_only
    assert gen.LESSON_COMPETITORS[rival_name] is gen._adjacent_equal_row_pairs_only
    assert gen.WITNESS_RIVALS["interleaved_rectangles"] == [rival_name]
    grid = interleaved_counterexample()
    assert gen.SEMANTIC_WITNESSES["interleaved_rectangles"](grid)
