from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.3031e2ee53d1.generator")


ROOT = find_root(__file__)


def _canonical_row():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, variant=0)
    return {
        "train": [pair for pair in pairs if pair["split"] == "train"],
        "test": [pair for pair in pairs if pair["split"] == "test"],
    }


def test_canonical_inputs_pass_and_python_mirror_matches_all_outputs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_schedule_covers_every_decisive_profile_in_every_four_window():
    expected = set(gen.SCHEDULE_PROFILES)
    profiles = [gen.schedule_profile(7, index) for index in range(12)]
    for start in range(9):
        assert set(profiles[start : start + 4]) == expected


def test_right_shift_regression_witness_and_exact_observation():
    grid = gen.generate(17, 1, difficulty="medium")
    facts = gen.semantic_observables(grid)
    assert facts["period"] == 2
    assert facts["shift"] == 2
    assert facts["shift_direction"] == "right"
    assert gen.rule_mirror(grid) != gen._rival_no_shift(grid)
    assert gen.observe_overrides(grid)["shift_direction"] == "right"


@pytest.mark.parametrize(
    "overrides",
    [
        {"width": 10, "height": 4, "period": 1, "shift_direction": "left", "color": 1},
        {"width": 16, "height": 8, "period": 3, "shift_direction": "right", "color": 9},
        {"width": 13, "height": 7, "period": 2, "shift_direction": "stationary", "color": 5},
    ],
)
def test_boundary_overrides_are_exact_and_rule_valid(overrides):
    grid = gen.generate(99, 8, difficulty="hard", **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert len(gen.rule_mirror(grid)) == overrides["width"]


def test_unknown_override_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(0, 0, typo_axis=3)


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(12345)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    changed = copy.deepcopy(first)
    changed[0][0] = (changed[0][0] + 1) % 10
    assert second != changed


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "all_background": [[0] * 10 for _ in range(5)],
        "full_one_color": [[3] * 10 for _ in range(5)],
        "singleton": [[3 if (r, c) == (2, 2) else 0 for c in range(10)] for r in range(5)],
        "short_line": [[3 if r == 2 and 2 <= c <= 5 else 0 for c in range(10)] for r in range(5)],
        "solid_2x2": [[3 if 1 <= r <= 2 and 1 <= c <= 2 else 0 for c in range(10)] for r in range(5)],
        "broken_recurrence": gen.generate(123, 1),
    }
    impostors["broken_recurrence"] = copy.deepcopy(impostors["broken_recurrence"])
    impostors["broken_recurrence"][3][0] = 7
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


@pytest.mark.parametrize("seed", [True, 1.0, "1"])
def test_generate_rejects_non_integer_seed(seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, 1.0, "1"])
def test_generate_rejects_non_integer_sample_index(sample_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(1, sample_index)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(1, -1)


@pytest.mark.parametrize(
    "seed,sample_index,error,match",
    [
        (True, 0, TypeError, "seed must be an integer"),
        (1.0, 0, TypeError, "seed must be an integer"),
        ("1", 0, TypeError, "seed must be an integer"),
        (1, True, TypeError, "sample_index must be an integer"),
        (1, 1.0, TypeError, "sample_index must be an integer"),
        (1, "1", TypeError, "sample_index must be an integer"),
        (1, -1, ValueError, "sample_index must be nonnegative"),
    ],
)
def test_schedule_profile_rejects_invalid_public_scalars(
    seed, sample_index, error, match
):
    with pytest.raises(error, match=match):
        gen.schedule_profile(seed, sample_index)
