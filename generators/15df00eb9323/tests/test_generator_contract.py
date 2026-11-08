"""Behavioral contract for the normalized majority-overlay base generator."""
from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "15df00eb9323"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _support_counts(grid):
    counts = {}
    for component in GEN.components(grid):
        for cell in component["norm"]:
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def test_metadata_exposes_only_truthful_controls():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_kind"}
    assert GEN.AXES["grid_h"]["valid"] == "7..14"
    assert GEN.AXES["grid_w"]["valid"] == "11..18"
    assert tuple(GEN.PALETTE_KINDS) == ("default", "warm", "cool", "varied")


def test_all_canonical_pairs_are_accepted_and_solved_exactly():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert set(_support_counts(pair["input"]).values()) == {1, 2, 3}
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("axis,value", [
    ("grid_h", 7), ("grid_h", 14),
    ("grid_w", 11), ("grid_w", 18),
])
def test_exact_dimension_boundaries_round_trip(difficulty, axis, value):
    grid = GEN.generate(20261025, 17, difficulty=difficulty, **{axis: value})
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("palette_kind", ["default", "warm", "cool", "varied"])
def test_palette_kind_is_observable_and_exact(palette_kind):
    grid = GEN.generate(991, 3, palette_kind=palette_kind)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["palette_kind"] == palette_kind


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_literal_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, 1.75, "1"])
def test_sample_index_requires_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid__"])
def test_difficulty_is_closed_typed_enum(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
@pytest.mark.parametrize("value", [True, False, 7.0, 7.5, "7"])
def test_integer_axes_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


@pytest.mark.parametrize("value", [True, 0, "hot", 1.0])
def test_palette_axis_rejects_unknown_or_wrong_typed_values(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, palette_kind=value)


def test_retired_dead_controls_and_out_of_range_values_are_rejected():
    for kwargs in (
        {"n_objects": 3}, {"palette_size": 3}, {"position_bias": "horizontal_three"},
        {"n_distinct_colors": 3}, {"density": "sparse"}, {"texture": "default"},
        {"grid_h": 6}, {"grid_h": 15}, {"grid_w": 10}, {"grid_w": 19},
        {"unknown_axis": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_scenes_have_single_pair_and_triple_support_and_are_identifiable(difficulty):
    demos = []
    for index in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(44617, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert set(_support_counts(grid).values()) == {1, 2, 3}
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(44618, GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    assert GEN.lesson_identifiable(demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}) == []


def test_none_override_is_unpinned_and_generation_is_fresh_rng_pure():
    state = random.getstate()
    baseline = GEN.generate(1234, 5)
    assert GEN.generate(1234, 5, grid_h=None) == baseline
    changed = GEN.generate(1234, 5)
    changed[0][0] = 9 if changed[0][0] != 9 else 1
    again = GEN.generate(1234, 5)
    assert again == baseline
    assert again is not baseline
    assert all(a is not b for a, b in zip(again, baseline))
    assert random.getstate() == state
