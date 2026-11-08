"""Focused regression tests for the nearest-marker rectangle sampler."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _components(grid, color=5):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while unseen:
        todo = [unseen.pop()]
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    todo.append(point)
        result.append(cells)
    return result


def _different_color_ties(grid):
    markers = [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 5)]
    ties = []
    for cells in _components(grid):
        cols = [c for _, c in cells]
        center = (min(cols) + max(cols)) // 2
        distances = [(abs(col - center), color) for col, color in markers]
        best = min(distance for distance, _ in distances)
        colors = {color for distance, color in distances if distance == best}
        if len(colors) > 1:
            ties.append((center, tuple(sorted(colors))))
    return ties


def test_tie_helper_returns_the_hand_checked_center_and_colors():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][2] = 4
    grid[0][4] = 6
    for row in range(3, 6):
        for col in range(2, 5):
            grid[row][col] = 5
    assert _different_color_ties(grid) == [(3, (4, 6))]


def test_retained_seed_no_longer_emits_an_undefined_nearest_marker_tie():
    grid = GEN.generate(0, 0)
    assert _different_color_ties(grid) == []


def test_validator_rejects_exact_ties_between_different_marker_colors():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][2] = 4
    grid[0][4] = 6
    for row in range(3, 6):
        for col in range(2, 5):
            grid[row][col] = 5
    assert any("tie" in reason.lower() for reason in GEN.self_check(grid))


def test_exact_n_rects_override_is_realized_without_silent_shortening():
    grid = GEN.generate(10, 1, n_rects=3, n_markers=4, palette_kind="cool")
    assert len(_components(grid)) == 3


def test_marker_colors_remain_distinct_for_every_advertised_count():
    grid = GEN.generate(10, 0, n_markers=4, palette_kind="cool")
    markers = [value for value in grid[0] if value not in (0, 5)]
    assert len(markers) == 4
    assert len(set(markers)) == 4


def test_rule_authority_hash_is_pinned():
    assert GEN.RULE_HASH == "5abbdbb61293"


def test_only_lawful_exact_controls_are_advertised():
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_markers",
        "n_rects",
        "marker_layout",
        "rect_size_kind",
        "palette_kind",
    }


def test_no_phantom_texture_profiles_are_advertised():
    assert GEN.HELPFUL_TEXTURES == ()


def test_large_profile_reaches_the_canonical_object_scale():
    grid = GEN.generate(
        4401,
        13,
        grid_h=10,
        grid_w=10,
        n_markers=2,
        n_rects=3,
        marker_layout="left_biased",
        rect_size_kind="large",
        palette_kind="small",
    )
    assert max(map(len, _components(grid))) >= 14


@pytest.mark.parametrize(
    "kwargs",
    [
        {"texture": "single_marker"},
        {"anchor_corner": True},
        {"typo_axis": 1},
        {"grid_h": True},
        {"n_rects": 2.0},
    ],
)
def test_invalid_or_retired_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_scalars_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)

# Broader contract and semantic tests use an independent task-local oracle.
import sys
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    observed as independently_observed,
    reference_output,
    rival_rank_order,
    rival_vertical_overlap_only,
    tie_objects,
    witness_facts,
)


@pytest.mark.parametrize("pair", canonical_pairs(), ids=("train0", "train1", "train2", "test0"))
def test_canonical_pairs_are_owned_and_match_the_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


def test_even_width_objects_use_the_racket_integer_midpoint():
    grid = [
        [6, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 5, 5, 0, 0, 0],
        [0, 5, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert GEN.self_check(grid) == []
    expected = [row[:] for row in grid]
    for row in (2, 3):
        expected[row][1] = expected[row][2] = 6
    assert reference_output(grid) == expected


def test_validator_rejects_floor_midpoint_tie_reproduced_by_semantic_gate():
    rows = (
        "6030900000", "0000000000", "0055055000", "0055055000",
        "0000000000", "0000000000", "0000000000", "0000000000",
        "0550000000", "0550000000",
    )
    grid = [[int(value) for value in row] for row in rows]
    assert any("tie" in reason.lower() for reason in GEN.self_check(grid))


def test_default_schedule_meets_the_canonical_profile_floor_census():
    hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{GEN.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile == (10, 10, 5)
            total += 1
    assert total == 60
    assert hits >= 15


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "expected",
    [
        dict(grid_h=10, grid_w=10, n_markers=2, n_rects=2,
             marker_layout="left_biased", rect_size_kind="small", palette_kind="warm"),
        dict(grid_h=18, grid_w=20, n_markers=4, n_rects=3,
             marker_layout="right_biased", rect_size_kind="large", palette_kind="cool"),
        dict(grid_h=12, grid_w=14, n_markers=3, n_rects=3,
             marker_layout="edges", rect_size_kind="varied", palette_kind="broad"),
        dict(grid_h=11, grid_w=13, n_markers=4, n_rects=2,
             marker_layout="evenly_spaced", rect_size_kind="medium", palette_kind="small"),
        dict(grid_h=13, grid_w=17, n_markers=3, n_rects=3,
             marker_layout="scattered", rect_size_kind="small", palette_kind="cool"),
    ],
)
def test_every_exact_control_round_trips_from_pixels_in_every_band(band, expected):
    grid = GEN.generate(1701, 29, difficulty=band, **expected)
    assert GEN.self_check(grid) == []
    assert independently_observed(grid) == expected
    assert GEN.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 9}, {"grid_h": 19}, {"grid_w": 9}, {"grid_w": 21},
        {"n_markers": 1}, {"n_markers": 5}, {"n_rects": 1}, {"n_rects": 4},
        {"marker_layout": "diagonal"}, {"rect_size_kind": "huge"},
        {"palette_kind": "mono"}, {"palette_kind": 1},
    ],
)
def test_out_of_domain_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["trivial", 1, True])
def test_invalid_difficulty_values_are_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_sampler_is_lawful_deterministic_and_observable(band):
    seen = set()
    for index in range(120):
        grid = GEN.generate(8100 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert tie_objects(grid) == []
        assert GEN.observe_overrides(grid) == independently_observed(grid)
        assert grid == GEN.generate(8100 + index, index, difficulty=band)
        seen.add(repr(grid))
    assert len(seen) >= 100


def test_returned_grids_are_fresh_objects():
    first = GEN.generate(43, 7)
    pristine = GEN.generate(43, 7)
    first[0][0] = 99
    assert GEN.generate(43, 7) == pristine


def test_declared_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs()
    assert all(rival_rank_order(pair["input"]) == pair["output"] for pair in pairs)
    assert all(rival_vertical_overlap_only(pair["input"]) == pair["output"] for pair in pairs)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"rank_order", "vertical_overlap_only"}
    for name, solver in GEN.CANONICAL_SHORTCUTS.items():
        assert all(solver(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_lesson_refutes_both_declared_shortcuts_under_all_rotations(band):
    for start in range(18):
        lesson = []
        for offset in range(3):
            index = start * 3 + offset
            grid = GEN.generate(23000 + start, index, difficulty=band)
            facts = witness_facts(grid)
            assert facts == {"shared_nearest": True, "nearest_outside_bbox": True}
            lesson.append({"input": grid, "output": reference_output(grid)})
        for query_index, query in enumerate(lesson):
            demos = lesson[:query_index] + lesson[query_index + 1:]
            assert GEN.lesson_identifiable(demos, query) == []
            for solver in GEN.LESSON_COMPETITORS.values():
                assert any(solver(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize(
    "mutation",
    ["tie", "duplicate_marker_color", "stray_color", "nonrect_component", "row1_nonblank"],
)
def test_validator_rejects_semantically_destructive_mutations(mutation):
    grid = GEN.generate(91, 4, grid_h=12, grid_w=14, n_markers=3, n_rects=3,
                        marker_layout="evenly_spaced", rect_size_kind="small",
                        palette_kind="warm")
    if mutation == "tie":
        grid = [[0] * 9 for _ in range(9)]
        grid[0][2], grid[0][4] = 4, 6
        for r in range(3, 6):
            for c in range(2, 5):
                grid[r][c] = 5
    elif mutation == "duplicate_marker_color":
        positions = [c for c, value in enumerate(grid[0]) if value not in (0, 5)]
        grid[0][positions[1]] = grid[0][positions[0]]
    elif mutation == "stray_color":
        grid[-1][-1] = 8
    elif mutation == "nonrect_component":
        cell = _components(grid)[0][0]
        grid[cell[0]][cell[1]] = 0
    elif mutation == "row1_nonblank":
        grid[1][0] = 5
    assert GEN.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert GEN.self_check(grid)
