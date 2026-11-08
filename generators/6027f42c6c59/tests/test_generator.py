"""Regression tests for the per-row leftmost-selection generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "6027f42c6c59"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
AXIS_NAMES = {"grid_h", "grid_w", "active_rows", "palette_size", "row_mode"}


def independent_rule(grid):
    """Hand-written mirror: preserve only the first nonzero value per row."""
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                output[row_index][col_index] = value
                break
    return output


def labelled(grid):
    return {"input": deepcopy(grid), "output": independent_rule(grid)}


def test_contract_is_pinned_and_only_observable_independent_axes_are_advertised():
    assert GEN.RULE_HASH == "e747e7753254"
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == AXIS_NAMES
    assert tuple(GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert set(GEN.SEMANTIC_RIVALS) == {
        "rightmost_per_row",
        "keep_everything",
        "global_leftmost_only",
    }


def test_all_canonical_pairs_are_accepted_and_match_independent_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for item in pairs:
        original = deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == original


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("grid_h", (5, 8))
@pytest.mark.parametrize("grid_w", (6, 10))
@pytest.mark.parametrize("active_rows", (4, 5))
@pytest.mark.parametrize("palette_size", (1, 7))
@pytest.mark.parametrize("row_mode", ("mixed", "all_multi"))
def test_every_axis_boundary_combination_round_trips(
    difficulty, grid_h, grid_w, active_rows, palette_size, row_mode
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "active_rows": active_rows,
        "palette_size": palette_size,
        "row_mode": row_mode,
    }
    grid = GEN.generate(7301, 11, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) == independent_rule(grid)
    assert independent_rule(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 9},
        {"grid_h": True},
        {"grid_h": 5.0},
        {"grid_h": "5"},
        {"grid_w": 5},
        {"grid_w": 11},
        {"active_rows": 3},
        {"active_rows": 6},
        {"active_rows": False},
        {"palette_size": 0},
        {"palette_size": 8},
        {"palette_size": 2.0},
        {"row_mode": "single"},
        {"row_mode": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ("expert", 0.5, True))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", (True, 1.0, "1"))
def test_invalid_seed_is_rejected(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", (-1, True, False, 1.0, "1"))
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_draws_are_lawful_observable_and_rule_visible(difficulty):
    seen = set()
    for index in range(24):
        grid = GEN.generate(1000 + 17 * index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert GEN.rule_mirror(grid) == independent_rule(grid)
        assert GEN.rule_mirror(grid) != grid
        seen.add(tuple(sorted(observed.items())))
    assert len(seen) >= 4



CANONICAL_PROFILES = {(5, 8, 7), (6, 7, 7), (6, 8, 8), (7, 6, 7)}


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_schedule_hits_every_exact_canonical_dimension_palette_profile(difficulty):
    profiles = set()
    for index in range(20):
        grid = GEN.generate(2400 + index, index, difficulty=difficulty)
        profiles.add((len(grid), len(grid[0]), len({value for row in grid for value in row})))
    assert CANONICAL_PROFILES <= profiles
    assert {profile[2] - 1 for profile in profiles} == set(range(1, 8))


def test_six_color_default_profiles_preserve_five_and_remove_one_color():
    for index in (0, 2, 6):
        grid = GEN.generate(3100 + index, index, difficulty="medium")
        before = {value for row in grid for value in row if value}
        after_grid = independent_rule(grid)
        after = {value for row in after_grid for value in row if value}
        assert len(before) == 6
        assert len(after) == 5
        assert len(before - after) == 1


def _object_stats(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    sizes = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        todo = [start]
        size = 0
        while todo:
            row, col = todo.pop()
            size += 1
            for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    todo.append(nxt)
        sizes.append(size)
    output = independent_rule(grid)
    persistent = 0
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells = [start]
        todo = [start]
        while todo:
            row, col = todo.pop()
            for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    cells.append(nxt)
                    todo.append(nxt)
        if len(cells) == 1:
            row, col = cells[0]
            persistent += output[row][col] == color
    return len(sizes), sum(size == 1 for size in sizes), persistent


def test_default_six_color_profiles_match_canonical_object_and_marker_support():
    for difficulty in BANDS:
        for index in (0, 2, 6):
            grid = GEN.generate(6300 + index, index, difficulty=difficulty)
            object_count, marker_count, persistent_markers = _object_stats(grid)
            assert object_count in {7, 8, 9}
            assert marker_count in {5, 6, 7, 8}
            assert persistent_markers == 4


def test_difficulty_changes_default_scene_without_changing_profile_support():
    for index in range(8):
        easy = GEN.generate(500, index, difficulty="easy")
        hard = GEN.generate(500, index, difficulty="hard")
        assert easy != hard
        assert GEN.self_check(easy) == []
        assert GEN.self_check(hard) == []

def test_every_generated_scene_refutes_each_declared_semantic_rival():
    for index in range(16):
        grid = GEN.generate(9000 + index, index, difficulty="hard")
        truth = independent_rule(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) != truth, (index, name)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert witness(grid), (index, name)


@pytest.mark.parametrize("difficulty", BANDS)
def test_two_demonstrations_identify_the_per_row_leftmost_rule(difficulty):
    for start in range(8):
        pairs = [
            labelled(GEN.generate(4000 + start, start + offset, difficulty=difficulty))
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        demos, query = pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]
        assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_semantically_empty_or_malformed_impostors():
    good = GEN.generate(
        17,
        4,
        grid_h=6,
        grid_w=8,
        active_rows=5,
        palette_size=4,
        row_mode="mixed",
    )
    assert GEN.self_check(good) == []

    no_multi = [[0 for _ in range(8)] for _ in range(6)]
    for row, col in enumerate((1, 2, 3, 4, 5)):
        no_multi[row][col] = (row % 4) + 1

    cases = [
        [],
        [[0] * 8 for _ in range(6)],
        [[1] * 8 for _ in range(6)],
        [[0, 0, 0], [0, 0]],
        [[True, 0, 0, 0, 0, 0] for _ in range(5)],
        no_multi,
    ]
    for grid in cases:
        assert GEN.self_check(grid), grid


def test_declared_mutation_fixtures_are_all_rejected():
    fixtures = GEN.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(777, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 13, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(777, 13, difficulty="hard") == second


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(808, 6)
    original = deepcopy(grid)
    GEN.observe_overrides(grid)
    GEN.strict_canonical_like(grid)
    GEN.rule_mirror(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == original
