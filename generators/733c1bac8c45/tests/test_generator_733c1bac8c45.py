"""Contract and semantic regressions for row-wise left packing.

The tests use literal expectations and canonical labels.  The Python mirror is
only a diagnostic cross-check; the repository's Racket rule remains authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "733c1bac8c45"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("left_pack_contract_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

ROOT = find_root(__file__)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def _active_rows(grid):
    return [row for row in grid if any(value != 0 for value in row)]


def _valid_hand_grid():
    return [
        [0, 1, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 2, 0, 2, 0],
        [0, 0, 3, 0, 0, 0, 0],
    ]


def test_all_canonical_inputs_are_owned_and_labels_match_the_mirror():
    assert len(CANONICAL) == 4
    for pair in CANONICAL:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_rule_mirror_counts_nonzeros_and_uses_the_first_nonzero_color():
    grid = [
        [0, 5, 0, 7, 0, 5],
        [0, 0, 0, 0, 0, 0],
        [8, 0, 8, 0, 8, 0],
        [0, 4, 0, 0, 0, 0],
    ]
    assert gen.rule_mirror(grid) == [
        [5, 5, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [8, 8, 8, 0, 0, 0],
        [4, 0, 0, 0, 0, 0],
    ]


def test_schedule_period_matches_the_public_profile_cycle():
    assert gen.LESSON_SCHEDULE_PERIOD == len(gen.SCHEDULE_PROFILES) == 4


@pytest.mark.parametrize("band", BANDS)
def test_default_four_profile_cycle_contains_two_tall_many_counterexamples(band):
    grids = [gen.generate(41, index, difficulty=band) for index in range(4)]
    assert [gen.schedule_profile(41, index, band) for index in range(4)] == list(
        gen.SCHEDULE_PROFILES
    )
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert observed[0] == {"grid_h": 5, "grid_w": 8, "active_rows": 3}
    assert observed[1] == {"grid_h": 5, "grid_w": 9, "active_rows": 4}
    assert all(item["grid_h"] > 5 and item["active_rows"] > 4 for item in observed[2:])
    assert all(gen.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", BANDS)
def test_every_default_query_rotation_is_identifiable(band):
    lesson = []
    for index in range(4):
        grid = gen.generate(19, index, difficulty=band)
        lesson.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(lesson) if index != query_index]
        assert gen.lesson_identifiable(demos, lesson[query_index]) == []


@pytest.mark.parametrize("bad_demos,bad_query,role", [
    ([{}], None, "demo 0"),
    (None, {}, "query"),
])
def test_lesson_identifiable_reports_malformed_pairs_without_crashing(
    bad_demos, bad_query, role
):
    grid = gen.generate(31, 2)
    valid_pair = {"input": grid, "output": gen.rule_mirror(grid)}
    demos = bad_demos if bad_demos is not None else [valid_pair]
    query = bad_query if bad_query is not None else valid_pair

    reasons = gen.lesson_identifiable(demos, query)

    assert any(role in reason and "must contain input and output" in reason for reason in reasons)


@pytest.mark.parametrize("band", BANDS)
def test_generated_inputs_fire_core_witnesses_and_tall_profiles_fire_shortcuts(band):
    grids = [gen.generate(7, index, difficulty=band) for index in range(4)]
    for grid in grids:
        assert gen.SEMANTIC_WITNESSES["visible_leftward_motion"](grid)
        assert gen.SEMANTIC_WITNESSES["multiple_moving_rows"](grid)
        assert gen.SEMANTIC_WITNESSES["internal_gap_collapse"](grid)
        assert gen.SEMANTIC_WITNESSES["multi_column_travel"](grid)
        assert gen.SEMANTIC_WITNESSES["variable_row_cardinality"](grid)
    for grid in grids[2:]:
        assert gen.SEMANTIC_WITNESSES["active_row_below_five"](grid)
        assert gen.SEMANTIC_WITNESSES["more_than_four_active_rows"](grid)
        expected = gen.rule_mirror(grid)
        for shortcut in gen.CANONICAL_SHORTCUTS.values():
            assert shortcut(grid) != expected


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width,active_rows", [
    (4, 5, 3),
    (6, 8, 5),
    (12, 14, 9),
])
def test_joint_axis_overrides_are_exact(height, width, active_rows, band):
    grid = gen.generate(
        73,
        11,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        active_rows=active_rows,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "active_rows": active_rows,
    }
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("key,value", [
    ("grid_h", 4),
    ("grid_h", 12),
    ("grid_w", 5),
    ("grid_w", 14),
    ("active_rows", 3),
    ("active_rows", 9),
])
def test_single_axis_boundaries_choose_feasible_other_axes(key, value, band):
    grid = gen.generate(29, 6, difficulty=band, **{key: value})
    assert gen.observe_overrides(grid)[key] == value
    assert gen.self_check(grid) == []


def test_impossible_height_and_active_row_request_names_both_axes():
    with pytest.raises(ValueError) as caught:
        gen.generate(0, 0, grid_h=4, active_rows=5)
    assert set(caught.value.incompatible_axes) == {"grid_h", "active_rows"}


@pytest.mark.parametrize("key,value", [
    ("grid_h", 3),
    ("grid_h", 13),
    ("grid_h", True),
    ("grid_h", 5.0),
    ("grid_w", 4),
    ("grid_w", 15),
    ("grid_w", False),
    ("active_rows", 2),
    ("active_rows", 10),
    ("active_rows", True),
])
def test_invalid_override_values_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(3, 2, **{key: value})


def test_unknown_and_retired_overrides_are_rejected():
    for key, value in (("unknown", 1), ("texture", "default"), ("palette_size", 3)):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(3, 2, **{key: value})


@pytest.mark.parametrize("key", ["grid_h", "grid_w", "active_rows"])
def test_none_uses_the_shared_unset_override_convention(key):
    assert gen.generate(12, 7, difficulty="hard", **{key: None}) == gen.generate(
        12, 7, difficulty="hard"
    )


@pytest.mark.parametrize("seed,index", [(0, 0), (9, 3), (91, 27)])
def test_generation_is_deterministic(seed, index):
    assert gen.generate(seed, index, difficulty="medium") == gen.generate(
        seed, index, difficulty="medium"
    )


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3])
def test_unknown_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed,index", [(True, 0), (1, True), (1, -1), (1.0, 0)])
def test_invalid_seed_or_sample_index_is_rejected(seed, index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, index)


def test_observer_recovers_literal_axes_from_a_hand_written_grid():
    grid = _valid_hand_grid()
    assert gen.observe_overrides(grid) == {"grid_h": 4, "grid_w": 7, "active_rows": 3}


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0, 1], [0]],
    [[0, 1], None],
    [[0, 1], [0, 2.5]],
    [[0, 1], [0, True]],
])
def test_malformed_grids_are_rejected(grid):
    assert gen.self_check(grid)
    with pytest.raises(ValueError):
        gen.observe_overrides(grid)


def test_self_check_rejects_multi_color_rows_duplicate_row_colors_and_weak_scenes():
    multi_color = _valid_hand_grid()
    multi_color[0][3] = 4
    assert any("one nonzero color" in reason for reason in gen.self_check(multi_color))

    duplicate = _valid_hand_grid()
    duplicate[2] = [1 if value == 2 else value for value in duplicate[2]]
    assert any("distinct" in reason for reason in gen.self_check(duplicate))

    too_few_rows = _valid_hand_grid()
    too_few_rows[3] = [0] * len(too_few_rows[3])
    assert any("active rows" in reason for reason in gen.self_check(too_few_rows))

    already_packed = [
        [1, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0],
        [3, 3, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("leftward packing" in reason for reason in gen.self_check(already_packed))


def test_every_mutation_fixture_is_rejected_by_the_teaching_grammar():
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_declared_canonical_shortcuts_reproduce_every_canonical_label():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "fixed_five_rows",
        "first_four_active_rows_only",
    }
    for pair in CANONICAL:
        for shortcut in gen.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]


def test_legacy_alias_axes_are_not_public_contract():
    assert set(gen.AXES) == {"grid_h", "grid_w", "active_rows"}
    grid = gen.generate(4, 2)
    assert set(gen.observe_overrides(grid)) == set(gen.AXES)
