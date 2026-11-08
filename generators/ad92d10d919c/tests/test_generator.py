"""Task-local regression suite for ad92d10d919c."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TASK_ID,
    any_four_nonzero_rival,
    at_least_three_rival,
    classify_centers,
    four_connected_object_count,
    load_generator,
    observed,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted():
    assert gen.RULE_HASH == "2fadbb67030c"
    assert gen.VERSION == "3.0.0"
    assert len(PAIRS) == 4
    for pair in PAIRS:
        before = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6, "grid_w": 7, "motif_count": 3},
        {"grid_h": 16, "grid_w": 18, "motif_count": 1},
        {"grid_h": 7, "grid_w": 9, "motif_count": 2},
    ],
)
def test_exact_controls_are_constructive_and_observable_in_every_band(band, overrides):
    grid = gen.generate(2, 0, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 5},
        {"grid_h": 17},
        {"grid_w": 6},
        {"grid_w": 19},
        {"motif_count": 0},
        {"motif_count": 4},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"motif_count": "2"},
        {"motif_count": None},
    ],
)
def test_invalid_or_unknown_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (0, -1, None),
        (0, 1.0, None),
        (0, 0, "extreme"),
    ],
)
def test_invalid_call_scalars_fail_loudly(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_has_exactly_one_scheduled_negative_control(band):
    inputs = set()
    canonical_like = 0
    for index in range(64):
        grid = gen.generate(20_000 + index, index, difficulty=band)
        facts = classify_centers(grid)
        assert gen.self_check(grid, difficulty=band) == []
        assert 1 <= len(facts["positive"]) <= 3
        assert len(facts["partial"]) == (index % 2 == 0)
        assert len(facts["mixed"]) == (index % 2 == 1)
        assert grid == gen.generate(20_000 + index, index, difficulty=band)
        inputs.add(frozen(grid))
        canonical_like += gen.strict_canonical_like(grid) == []
    assert len(inputs) >= 60
    assert canonical_like >= 12



def test_mixed_schedule_is_a_canonical_profile_and_matches_coarse_authority_structure():
    for band in [None, "easy", "medium", "hard"]:
        grid = gen.generate(1, 1, difficulty=band)
        palette_size = len({value for row in grid for value in row})
        assert (len(grid), len(grid[0]), palette_size) == (6, 8, 3)
        assert four_connected_object_count(grid) == 8
        assert len(classify_centers(grid)["positive"]) == 1
        assert len(classify_centers(grid)["mixed"]) == 1

def test_audit_seed_no_longer_silently_drops_requested_motifs():
    grid = gen.generate(2, 0, difficulty="easy", grid_h=6, grid_w=7, motif_count=3)
    assert observed(grid)["motif_count"] == 3
    assert gen.self_check(grid) == []


def test_canonical_shortcuts_fit_authority_but_generated_controls_refute_them():
    assert all(at_least_three_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(any_four_nonzero_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(32):
        grid = gen.generate(31_000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        official = rule_output(grid)
        if index % 2 == 0:
            assert at_least_three_rival(grid) != official
        else:
            assert any_four_nonzero_rival(grid) != official


def test_every_four_pair_window_remains_identifiable_after_any_query_holdout():
    for band in [None, "easy", "medium", "hard"]:
        grids = [gen.generate(44, index, difficulty=band) for index in range(12)]
        for start in range(9):
            pairs = grids[start : start + 4]
            for query_index in range(4):
                demos = [grid for i, grid in enumerate(pairs) if i != query_index]
                assert any(at_least_three_rival(grid) != rule_output(grid) for grid in demos)
                assert any(any_four_nonzero_rival(grid) != rule_output(grid) for grid in demos)


def test_declared_semantic_contract_matches_independent_oracles():
    assert set(gen.SEMANTIC_WITNESSES) == {
        "positive_consensus",
        "three_of_four_near_miss",
        "mixed_four_near_miss",
    }
    assert set(gen.SEMANTIC_RIVALS) == {"at_least_three", "any_four_nonzero"}
    assert gen.CANONICAL_SHORTCUTS == gen.SEMANTIC_RIVALS
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS == {
        "three_of_four_near_miss": ["at_least_three"],
        "mixed_four_near_miss": ["any_four_nonzero"],
    }
    for index in range(20):
        grid = gen.generate(50_000 + index, index)
        facts = classify_centers(grid)
        assert gen.SEMANTIC_WITNESSES["positive_consensus"](grid) is bool(facts["positive"])
        assert gen.SEMANTIC_WITNESSES["three_of_four_near_miss"](grid) is bool(facts["partial"])
        assert gen.SEMANTIC_WITNESSES["mixed_four_near_miss"](grid) is bool(facts["mixed"])
        assert gen.SEMANTIC_RIVALS["at_least_three"](grid) == at_least_three_rival(grid)
        assert gen.SEMANTIC_RIVALS["any_four_nonzero"](grid) == any_four_nonzero_rival(grid)


def test_validator_rejects_minimal_structural_impostors():
    impostors = [
        [[0] * 7 for _ in range(6)],
        [[1] + [0] * 6] + [[0] * 7 for _ in range(5)],
        [[1, 1] + [0] * 5, [1, 1] + [0] * 5] + [[0] * 7 for _ in range(4)],
        [[1, 1, 1] + [0] * 4] + [[0] * 7 for _ in range(5)],
    ]
    for grid in impostors:
        assert gen.self_check(grid), grid


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(6)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_replay_is_fresh_and_does_not_touch_global_random_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
