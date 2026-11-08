"""Focused contract and inherited-defect regressions for Largest Crop."""
from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "2786bc764238"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_canonical_pairs_remain_inside_domain_and_match_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_integer_axis_boundaries_round_trip(difficulty):
    for axis, values in {
        "grid_h": (9, 12),
        "grid_w": (12, 15),
        "component_count": (2, 5),
        "largest_size": (6, 11),
    }.items():
        for value in values:
            grid = GEN.generate(44617, 9, difficulty=difficulty, **{axis: value})
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.observe_overrides(grid)[axis] == value


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


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "component_count", "largest_size"])
@pytest.mark.parametrize("value", [True, False, 6.0, 6.75, "6"])
def test_integer_axes_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


def test_unknown_and_out_of_range_overrides_are_rejected():
    for kwargs in (
        {"typo": 1},
        {"grid_h": 8}, {"grid_h": 13},
        {"grid_w": 11}, {"grid_w": 16},
        {"component_count": 1}, {"component_count": 6},
        {"largest_size": 5}, {"largest_size": 9}, {"largest_size": 12},
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **kwargs)


def test_none_override_is_unpinned_and_generation_is_fresh_rng_pure():
    state = random.getstate()
    baseline = GEN.generate(1234, 5)
    assert GEN.generate(1234, 5, grid_h=None) == baseline
    mutated = GEN.generate(1234, 5)
    mutated[0][0] = 9 if mutated[0][0] != 9 else 1
    again = GEN.generate(1234, 5)
    assert again == baseline
    assert again is not baseline
    assert all(a is not b for a, b in zip(again, baseline))
    assert random.getstate() == state
