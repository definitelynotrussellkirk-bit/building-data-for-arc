"""Focused regressions for the reviewed first-found-color generator.

These tests intentionally use an independent rule implementation and recover
all exact controls from pixels.  They run both in the source tree and in the
portable copied runtime used by ``arcpuzzles check --stage task_tests``.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import random
import sys

import pytest


for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


TASK_ID = "341758fa9de1"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SPEC = importlib.util.spec_from_file_location(
    f"review_contract_{TASK_ID}", GENERATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def independent_rule(grid):
    """Keep every occurrence of the row-major first nonzero color."""
    key = next((value for row in grid for value in row if value != 0), None)
    if key is None:
        return [row[:] for row in grid]
    return [[value if value == key else 0 for value in row] for row in grid]


def assert_arc_grid(grid):
    assert isinstance(grid, list) and grid and grid[0]
    width = len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


def nonzero_colors(grid):
    return {value for row in grid for value in row if value != 0}


def first_key(grid):
    return next(value for row in grid for value in row if value != 0)


def first_nonzero_position(grid):
    return next(
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 0
    )


def numeric_rank_profile(grid):
    colors = sorted(nonzero_colors(grid))
    rank = colors.index(first_key(grid))
    if rank == 0:
        return "low"
    if rank == len(colors) - 1:
        return "high"
    return "middle"


def first_occupied_row(grid):
    return next(row for row in grid if any(value != 0 for value in row))


def profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "6e591d69c073"


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=[f"{pair['split']}-{pair['pair_index']}" for pair in PAIRS],
)
def test_independent_rule_reproduces_and_self_check_accepts_canonical_pairs(pair):
    before = deepcopy(pair["input"])
    assert independent_rule(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "controls",
    [
        {"grid_h": 5},
        {"grid_h": 18},
        {"grid_w": 5},
        {"grid_w": 18},
        {"n_colors": 3},
        {"n_colors": 5},
        {"palette_kind": "cool"},
        {"palette_kind": "warm"},
        {"palette_kind": "varied"},
        {"key_frequency": "least"},
        {"key_frequency": "middle"},
        {"key_frequency": "most"},
        {
            "grid_h": 5,
            "grid_w": 5,
            "n_colors": 5,
            "palette_kind": "varied",
            "key_frequency": "middle",
        },
        {
            "grid_h": 18,
            "grid_w": 18,
            "n_colors": 3,
            "palette_kind": "warm",
            "key_frequency": "least",
        },
    ],
)
def test_every_declared_override_is_exact_in_every_difficulty(controls, difficulty):
    grid = gen.generate(1701, 29, difficulty=difficulty, **controls)
    assert_arc_grid(grid)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    for name, expected in controls.items():
        assert observed[name] == expected, (name, controls, observed)


@pytest.mark.parametrize(
    "controls",
    [
        {"__override_contract_unknown_axis__": 1},
        {"grid_h": 4},
        {"grid_h": 19},
        {"grid_h": "5"},
        {"grid_h": True},
        {"grid_w": 5.0},
        {"n_colors": 2},
        {"n_colors": 6},
        {"n_colors": False},
        {"palette_kind": "default"},
        {"palette_kind": 1},
        {"key_frequency": "median"},
        {"key_frequency": 1},
    ],
)
def test_invalid_and_unknown_controls_reject_loudly(controls):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 29, **controls)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_curriculum_anchors_all_canonical_profiles_in_each_band(difficulty):
    canonical_profiles = {profile(pair["input"]) for pair in PAIRS}
    seen = {
        profile(gen.generate(7001, sample_index, difficulty=difficulty))
        for sample_index in range(12)
    }
    assert canonical_profiles <= seen


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_scenes_make_the_rule_visible_and_refute_positional_shortcuts(difficulty):
    for sample_index in range(12):
        grid = gen.generate(9101, sample_index, difficulty=difficulty)
        assert_arc_grid(grid)
        assert gen.self_check(grid) == []
        key = first_key(grid)
        counts = Counter(value for row in grid for value in row if value != 0)
        assert counts[key] >= 2
        assert grid[0][0] == 0
        row = first_occupied_row(grid)
        assert next(value for value in row if value != 0) == key
        assert next(value for value in reversed(row) if value != 0) != key
        assert grid[-1][-1] != key and grid[-1][-1] != 0
        assert independent_rule(grid) != grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_curriculum_varies_selector_position_and_numeric_rank(difficulty):
    grids = [gen.generate(12101, index, difficulty=difficulty) for index in range(12)]
    positions = {first_nonzero_position(grid) for grid in grids}
    ranks = {numeric_rank_profile(grid) for grid in grids}
    assert len(positions) >= 3, positions
    assert positions != {(0, 1)}
    assert ranks == {"low", "middle", "high"}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_four_sample_window_is_rotation_identifiable(difficulty):
    competitors = gen.LESSON_COMPETITORS
    assert set(competitors) >= {
        "most_frequent",
        "top_left_color",
        "rightmost_first_row_color",
        "fixed_position_0_1",
        "lowest_color",
        "middle_numeric_color",
        "highest_color",
    }
    for start in range(6):
        pairs = []
        for offset in range(4):
            grid = gen.generate(12317, start + offset, difficulty=difficulty)
            pairs.append({"input": grid, "output": independent_rule(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in competitors.items():
                fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                assert not fits or rival(query["input"]) == query["output"], (
                    difficulty,
                    start,
                    query_index,
                    name,
                )


def test_declared_canonical_shortcuts_really_fit_every_public_pair():
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in PAIRS:
            before = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], (name, pair)
            assert pair["input"] == before


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(91, 117, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(91, 117, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
