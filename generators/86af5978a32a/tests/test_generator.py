"""Regression tests for the layout-times-shape expansion generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "86af5978a32a"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {(3, 6, 5), (4, 8, 4), (8, 4, 5)}
AXIS_NAMES = {
    "half_size",
    "orientation",
    "layout_position",
    "n_layout_colors",
    "color_role",
}


def _split(grid):
    """Split by composition geometry without inferring semantic roles."""
    height = len(grid)
    width = len(grid[0])
    if width == 2 * height:
        k = height
        first = [row[:k] for row in grid]
        second = [row[k:] for row in grid]
        return "horizontal", k, first, second
    if height == 2 * width:
        k = width
        first = [list(row) for row in grid[:k]]
        second = [list(row) for row in grid[k:]]
        return "vertical", k, first, second
    raise ValueError(f"grid is not two equal square halves: {height}x{width}")


def _nonzero_colors(panel):
    return {value for row in panel for value in row if value != 0}


def independent_rule(grid):
    """Independent mirror of the canonical distinct-color role rule."""
    _orientation, k, first, second = _split(grid)
    first_colors = _nonzero_colors(first)
    second_colors = _nonzero_colors(second)
    if len(first_colors) > len(second_colors):
        layout, shape = first, second
    elif len(second_colors) > len(first_colors):
        layout, shape = second, first
    else:
        raise ValueError("the two halves do not have distinct role cardinalities")

    mask = [
        (row, col)
        for row in range(k)
        for col in range(k)
        if shape[row][col] != 0
    ]
    output = [[0 for _ in range(k * k)] for _ in range(k * k)]
    for layout_row in range(k):
        for layout_col in range(k):
            color = layout[layout_row][layout_col]
            if color == 0:
                continue
            for shape_row, shape_col in mask:
                output[layout_row * k + shape_row][layout_col * k + shape_col] = color
    return output


def labelled(grid):
    return {"input": deepcopy(grid), "output": independent_rule(grid)}


def load_counterexample(name):
    with (HOME / "counterexamples" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_contract_is_pinned_and_only_exact_observable_axes_are_advertised():
    assert GEN.RULE_HASH == "80100e676959"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == AXIS_NAMES
    assert tuple(GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert tuple(GEN.SCHEDULE_PROFILES) == (0, 1, 2, 3)
    assert set(GEN.SEMANTIC_RIVALS) == {
        "fixed_eight_shape",
        "first_half_is_layout",
        "horizontal_only",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == {"fixed_eight_shape"}


def test_all_canonical_pairs_are_accepted_and_match_an_independent_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 8
    for item in pairs:
        original = deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == original


def test_fixed_eight_shortcut_reproduces_every_labeled_canonical_pair():
    rival = GEN.CANONICAL_SHORTCUTS["fixed_eight_shape"]
    for item in canonical_pairs(TASK_ID, root=ROOT):
        assert rival(item["input"]) == item["output"]


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("half_size", (3, 5))
@pytest.mark.parametrize("orientation", ("horizontal", "vertical"))
@pytest.mark.parametrize("layout_position", ("first", "second"))
@pytest.mark.parametrize("n_layout_colors", (2, 4))
@pytest.mark.parametrize("color_role", ("shape_is_8", "layout_has_8"))
def test_every_axis_boundary_combination_round_trips(
    difficulty,
    half_size,
    orientation,
    layout_position,
    n_layout_colors,
    color_role,
):
    requested = {
        "half_size": half_size,
        "orientation": orientation,
        "layout_position": layout_position,
        "n_layout_colors": n_layout_colors,
        "color_role": color_role,
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
        {"half_size": 2},
        {"half_size": 6},
        {"half_size": True},
        {"half_size": 3.0},
        {"half_size": "3"},
        {"orientation": "diagonal"},
        {"orientation": 1},
        {"layout_position": "left"},
        {"layout_position": False},
        {"n_layout_colors": 1},
        {"n_layout_colors": 5},
        {"n_layout_colors": True},
        {"n_layout_colors": 3.0},
        {"color_role": "no_eight"},
        {"color_role": 8},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ("expert", 0.5, True))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("sample_index", (-1, True, False, 1.0, "1"))
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_band_has_exact_canonical_profile_support_in_twenty_draws(difficulty):
    profiles = set()
    for index in range(20):
        grid = GEN.generate(1000 + index * 17, index, difficulty=difficulty)
        profiles.add((len(grid), len(grid[0]), len({value for row in grid for value in row})))
    assert profiles <= CANONICAL_PROFILES
    assert profiles == CANONICAL_PROFILES


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_schedule_covers_every_branch_and_declared_witness(difficulty):
    observed = [
        GEN.observe_overrides(GEN.generate(5000 + index, index, difficulty=difficulty))
        for index in range(8)
    ]
    assert {row["orientation"] for row in observed} == {"horizontal", "vertical"}
    assert {row["layout_position"] for row in observed} == {"first", "second"}
    assert {row["color_role"] for row in observed} == {"shape_is_8", "layout_has_8"}
    assert {row["half_size"] for row in observed} == {3, 4}
    assert {row["n_layout_colors"] for row in observed} == {2, 3}
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(GEN.generate(5000 + index, index, difficulty=difficulty)) for index in range(8)), name


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_five_pair_window_and_query_rotation_is_identifiable(difficulty):
    for start in range(12):
        pairs = [
            labelled(GEN.generate(9000 + start, start + offset, difficulty=difficulty))
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        for query_index, query in enumerate(pairs):
            demos = [item for index, item in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(competitor(item["input"]) != item["output"] for item in demos), (
                    difficulty,
                    start,
                    query_index,
                    name,
                )


def test_exact_fixed_eight_counterexample_refutes_the_canonical_shortcut():
    case = load_counterexample("fixed_eight_shape.json")
    grid = case["input"]
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "half_size": 3,
        "orientation": "horizontal",
        "layout_position": "first",
        "n_layout_colors": 2,
        "color_role": "layout_has_8",
    }
    truth = independent_rule(grid)
    rival = GEN.CANONICAL_SHORTCUTS["fixed_eight_shape"]
    assert GEN.SEMANTIC_WITNESSES["eight_in_layout"](grid)
    assert rival(grid) != truth


@pytest.mark.parametrize(
    ("overrides", "witness", "rival"),
    [
        (
            {
                "half_size": 4,
                "orientation": "horizontal",
                "layout_position": "first",
                "n_layout_colors": 3,
                "color_role": "layout_has_8",
            },
            "eight_in_layout",
            "fixed_eight_shape",
        ),
        (
            {
                "half_size": 4,
                "orientation": "horizontal",
                "layout_position": "second",
                "n_layout_colors": 3,
                "color_role": "shape_is_8",
            },
            "layout_is_second",
            "first_half_is_layout",
        ),
        (
            {
                "half_size": 4,
                "orientation": "vertical",
                "layout_position": "first",
                "n_layout_colors": 3,
                "color_role": "layout_has_8",
            },
            "vertical_composition",
            "horizontal_only",
        ),
    ],
)
def test_each_semantic_witness_really_refutes_its_named_rival(overrides, witness, rival):
    grid = GEN.generate(811, 7, **overrides)
    truth = independent_rule(grid)
    assert GEN.SEMANTIC_WITNESSES[witness](grid)
    assert GEN.SEMANTIC_RIVALS[rival](grid) != truth
    assert rival in GEN.WITNESS_RIVALS[witness]


def test_self_check_rejects_malformed_or_semantically_empty_impostors():
    good = GEN.generate(
        17,
        4,
        half_size=4,
        orientation="horizontal",
        layout_position="first",
        n_layout_colors=3,
        color_role="layout_has_8",
    )
    assert GEN.self_check(good) == []

    cases = [
        [],
        [[0] * 8 for _ in range(4)],
        [[3] * 8 for _ in range(4)],
        [[3, 3], [3, 3]],
        [[0, 0, 0], [0, 0]],
        [[True, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
    ]

    no_shape = deepcopy(good)
    for row in range(4):
        for col in range(4, 8):
            no_shape[row][col] = 0
    cases.append(no_shape)

    no_layout = deepcopy(good)
    for row in range(4):
        for col in range(4):
            no_layout[row][col] = 0
    cases.append(no_layout)

    same_color_on_both_sides = deepcopy(good)
    shape_color = next(value for row in same_color_on_both_sides for value in row[4:] if value)
    layout_cell = next(
        (row, col)
        for row in range(4)
        for col in range(4)
        if same_color_on_both_sides[row][col] != 0
    )
    same_color_on_both_sides[layout_cell[0]][layout_cell[1]] = shape_color
    cases.append(same_color_on_both_sides)

    no_eight = deepcopy(good)
    for row in range(4):
        for col in range(8):
            if no_eight[row][col] == 8:
                no_eight[row][col] = 7
    cases.append(no_eight)

    one_shape_cell = deepcopy(good)
    shape_cells = [
        (row, col)
        for row in range(4)
        for col in range(4, 8)
        if one_shape_cell[row][col] != 0
    ]
    for row, col in shape_cells[1:]:
        one_shape_cell[row][col] = 0
    cases.append(one_shape_cell)

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


def test_public_schedule_contract_covers_declared_profiles():
    seen = {
        GEN.schedule_profile(123456, index, difficulty="hard")
        for index in range(len(GEN.SCHEDULE_PROFILES))
    }
    assert seen == set(GEN.SCHEDULE_PROFILES)
