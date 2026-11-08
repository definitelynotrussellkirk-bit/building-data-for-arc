"""Task-local regression suite for f8b9516df05e."""
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
    ignore_blocker_rival,
    load_generator,
    malformed_grids,
    observed,
    rule_output,
    skip_unit_gap_rival,
    teaching_errors,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted():
    assert getattr(gen, "RULE_HASH", None) == "d469cd5280c8"
    assert gen.VERSION == "4.1.0"
    assert len(PAIRS) == 5
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
        {"grid_h": 5, "grid_w": 7, "rays": 5, "post_blocker_cells": 3},
        {"grid_h": 14, "grid_w": 16, "rays": 1, "post_blocker_cells": 0},
        {"grid_h": 8, "grid_w": 9, "rays": 3, "post_blocker_cells": 2},
    ],
)
def test_exact_controls_are_constructive_and_observable_in_every_band(band, overrides):
    grid = gen.generate(1701, 29, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides
    assert teaching_errors(grid) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 4},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 17},
        {"rays": 0},
        {"rays": 6},
        {"post_blocker_cells": -1},
        {"post_blocker_cells": 4},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"rays": "3"},
        {"post_blocker_cells": None},
    ],
)
def test_invalid_or_unknown_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_sparse_canonical_centered_and_diverse(band):
    inputs = set()
    canonical_like = 0
    nonzero_counts = []
    for index in range(96):
        grid = gen.generate(9_100 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert teaching_errors(grid) == []
        assert grid == gen.generate(9_100 + index, index * 7 + 3, difficulty=band)
        inputs.add(frozen(grid))
        nonzero_counts.append(sum(value != 0 for row in grid for value in row))
        canonical_like += gen.strict_canonical_like(grid) == []
    assert len(inputs) >= 90
    assert max(nonzero_counts) <= 13
    assert sum(nonzero_counts) / len(nonzero_counts) <= 9.5
    assert canonical_like >= 20


def test_replay_is_fresh_and_does_not_touch_global_random_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_canonical_shortcut_fits_authority_but_generated_inputs_refute_it():
    assert all(skip_unit_gap_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(64):
        grid = gen.generate(8_100 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        official = rule_output(grid)
        assert skip_unit_gap_rival(grid) != official
        assert ignore_blocker_rival(grid) != official


def test_declared_semantic_contract_is_live_and_matches_independent_rivals():
    assert set(gen.SEMANTIC_WITNESSES) == {"unit_gap", "trailing_background", "first_vs_last_blocker"}
    assert set(gen.SEMANTIC_RIVALS) == {"skip_unit_gap", "ignore_blocker", "last_blocker"}
    assert set(gen.CANONICAL_SHORTCUTS) == {"skip_unit_gap", "last_blocker"}
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS == {
        "unit_gap": ["skip_unit_gap"],
        "trailing_background": ["ignore_blocker"],
        "first_vs_last_blocker": ["last_blocker"],
    }
    for index in range(48):
        grid = gen.generate(20_000 + index, index)
        official = rule_output(grid)
        assert gen.SEMANTIC_WITNESSES["unit_gap"](grid)
        assert gen.SEMANTIC_WITNESSES["trailing_background"](grid)
        assert gen.SEMANTIC_WITNESSES["first_vs_last_blocker"](grid) is (
            gen.observe_overrides(grid)["post_blocker_cells"] > 0)
        assert gen.SEMANTIC_RIVALS["skip_unit_gap"](grid) == skip_unit_gap_rival(grid)
        assert gen.SEMANTIC_RIVALS["ignore_blocker"](grid) == ignore_blocker_rival(grid)
        assert gen.SEMANTIC_RIVALS["skip_unit_gap"](grid) != official
        assert gen.SEMANTIC_RIVALS["ignore_blocker"](grid) != official
        assert (gen.SEMANTIC_RIVALS["last_blocker"](grid) != official) is (
            gen.observe_overrides(grid)["post_blocker_cells"] > 0)


@pytest.mark.parametrize("grid", malformed_grids())
def test_malformed_or_non_lesson_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_minimal_structural_impostors():
    valid = gen.generate(11, 5, grid_h=8, grid_w=10, rays=3, post_blocker_cells=0)
    mutations = []

    blank = [[0 for _ in row] for row in valid]
    mutations.append(blank)

    no_blocker = deepcopy(valid)
    for row in no_blocker:
        if any(value not in (0, 8) for value in row):
            for c, value in enumerate(row):
                if value == 8:
                    row[c] = 0
                    break
            break
    mutations.append(no_blocker)

    blocked_path = deepcopy(valid)
    for row in blocked_path:
        emitters = [c for c, value in enumerate(row) if value not in (0, 8)]
        blockers = [c for c, value in enumerate(row) if value == 8]
        if emitters and blockers and blockers[0] - emitters[0] > 1:
            row[emitters[0] + 1] = 9 if row[emitters[0]] != 9 else 7
            break
    mutations.append(blocked_path)

    leading_blocker = deepcopy(valid)
    for row in leading_blocker:
        emitters = [c for c, value in enumerate(row) if value not in (0, 8)]
        if emitters and emitters[0] > 0:
            row[emitters[0] - 1] = 8
            break
    mutations.append(leading_blocker)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation
