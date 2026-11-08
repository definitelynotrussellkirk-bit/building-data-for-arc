"""Source-bound regressions for the df3c6021b715 two-dot frame sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "df3c6021b715"
HOME = Path(__file__).resolve().parents[1]
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "color_pair",
    "upper_row_slot",
    "lower_row_slot",
    "upper_col_slot",
    "lower_col_slot",
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_df3c6021b715", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK, root=find_root(__file__))


def _dots(grid):
    return sorted(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    )


def _pair(input_grid, output_grid=None):
    return {
        "input": deepcopy(input_grid),
        "output": deepcopy(output_grid if output_grid is not None else gen._reference_output(input_grid)),
    }


def test_pins_selected_authority_and_advertises_only_exact_controls():
    assert gen.RULE_HASH == "77666531c7cb"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert not hasattr(gen, "DEGENERATE_TEXTURES")


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_python_oracle_matches_outputs(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    original = deepcopy(pair["input"])
    assert gen._reference_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_visible_in_every_band(band):
    expected = {
        "grid_h": 8,
        "grid_w": 18,
        "color_pair": 71,
        "upper_row_slot": 2,
        "lower_row_slot": 0,
        "upper_col_slot": 4,
        "lower_col_slot": 0,
    }
    grid = gen.generate(17, 29, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert _dots(grid) == [(3, 16, 9), (4, 1, 8)]


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 7),
        ("grid_h", 19),
        ("grid_w", True),
        ("color_pair", -1),
        ("color_pair", 72),
        ("upper_row_slot", 3),
        ("lower_row_slot", -1),
        ("upper_col_slot", 5),
        ("lower_col_slot", 2.0),
        ("color_pair", "7"),
    ],
)
def test_unknown_out_of_range_and_coercible_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_schedule_has_one_canonical_profile_anchor_and_three_teaching_profiles(band):
    names = [gen.schedule_profile(91, index, difficulty=band) for index in range(4)]
    assert names == list(gen.SCHEDULE_PROFILES)
    rows = [gen.observe_overrides(gen.generate(91, index, difficulty=band)) for index in range(4)]
    assert rows[0]["grid_h"] == rows[0]["grid_w"] == 10
    assert rows[0]["upper_row_slot"] == rows[0]["lower_row_slot"] == 1
    # Two of four scheduled profiles anchor the exact canonical morphology,
    # keeping the strict profile floor above its 25% clean-verdict threshold.
    assert sum(row["grid_h"] == row["grid_w"] == 10 for row in rows) == 2
    assert rows[2]["grid_h"] == rows[2]["grid_w"] == 10
    for row in rows[1:]:
        upper, lower = gen._COLOR_PAIRS[row["color_pair"]]
        assert upper > lower
    for index in (1, 3):
        grid = gen.generate(91, index, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["noncanonical_half_split"](grid)
    # The second canonical-scale profile still refutes row and colour shortcuts.
    profile_two = gen.generate(91, 2, difficulty=band)
    assert gen.SEMANTIC_WITNESSES["noncanonical_dot_rows"](profile_two)
    assert gen.SEMANTIC_WITNESSES["reversed_color_order"](profile_two)


def test_split_adjacent_rows_are_reachable_on_even_grids():
    grid = gen.generate(
        7,
        2,
        grid_h=8,
        grid_w=8,
        color_pair=0,
        upper_row_slot=2,
        lower_row_slot=0,
        upper_col_slot=2,
        lower_col_slot=2,
    )
    assert [dot[0] for dot in _dots(grid)] == [3, 4]
    assert gen.observe_overrides(grid)["upper_row_slot"] == 2
    assert gen.observe_overrides(grid)["lower_row_slot"] == 0


def test_split_adjacent_rows_are_reachable_on_odd_grids_at_integer_midpoint():
    grid = gen.generate(
        7,
        2,
        grid_h=11,
        grid_w=11,
        color_pair=0,
        upper_row_slot=2,
        lower_row_slot=0,
        upper_col_slot=2,
        lower_col_slot=2,
    )
    assert [dot[0] for dot in _dots(grid)] == [4, 5]
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["upper_row_slot"] == 2
    assert gen.observe_overrides(grid)["lower_row_slot"] == 0


def test_python_oracle_uses_racket_integer_division_on_odd_heights():
    grid = [[0] * 11 for _ in range(11)]
    grid[4][3] = 2
    grid[5][7] = 1
    expected = [[0] * 11 for _ in range(11)]
    for row in range(11):
        color = 2 if row < 5 else 1
        horizontal = row in (0, 4, 5, 10)
        for col in range(11):
            if horizontal or col in (0, 10):
                expected[row][col] = color
    assert gen.self_check(grid) == []
    assert gen._reference_output(grid) == expected
    assert not gen.SEMANTIC_WITNESSES["noncanonical_half_split"](grid)


@pytest.mark.parametrize("seed", [0, 1, 73, 9123])
def test_generation_is_deterministic_and_non_mutating(seed):
    first = gen.generate(seed, 13, difficulty="hard")
    before = deepcopy(first)
    assert first == gen.generate(seed, 13, difficulty="hard")
    gen.observe_overrides(first)
    gen._reference_output(first)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(first)
    assert first == before


def test_declared_shortcuts_fit_every_canonical_pair():
    assert PAIRS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert name in gen.SEMANTIC_RIVALS
        assert name in gen.LESSON_COMPETITORS
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


def test_each_declared_witness_is_a_real_counterexample():
    grid = gen.generate(103, 1, difficulty="medium")
    canonical = gen._reference_output(grid)
    for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert predicate(grid), witness_name
        rivals = gen.WITNESS_RIVALS[witness_name]
        assert rivals
        assert any(gen.SEMANTIC_RIVALS[name](grid) != canonical for name in rivals)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_every_cyclic_start_and_query_rotation_teaches_declared_rivals(band, start):
    pairs = []
    for offset in range(4):
        grid = gen.generate(404, start + offset, difficulty=band)
        pairs.append(_pair(grid))
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                band,
                start,
                query_index,
                name,
            )


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(7)] + [[11] + [0] * 7],
    ],
)
def test_malformed_and_out_of_domain_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_same_color_border_and_half_mutations():
    base = gen.generate(81, 2, grid_h=10, grid_w=10, color_pair=0)
    mutations = []

    same_color = deepcopy(base)
    dots = _dots(same_color)
    same_color[dots[1][0]][dots[1][1]] = dots[0][2]
    mutations.append(same_color)

    border = deepcopy(base)
    r, c, value = _dots(border)[0]
    border[r][c] = 0
    border[0][c] = value
    mutations.append(border)

    same_half = deepcopy(base)
    r, c, value = _dots(same_half)[1]
    same_half[r][c] = 0
    same_half[1][c] = value
    mutations.append(same_half)

    for grid in mutations:
        assert gen.self_check(grid)
