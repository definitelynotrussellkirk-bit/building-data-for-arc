"""Task-local regressions for the reviewed 26dbe76edccd generator."""
from __future__ import annotations

from copy import deepcopy
import random
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "26dbe76edccd"
ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
sys.path.insert(0, str(ROOT / "generators" / TASK_ID / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    malformed_grids,
    observed,
    rule_output,
    teaching_errors,
)

PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted():
    assert gen.RULE_HASH == "ff55fa477cae"
    assert gen.VERSION == "2.0.0"
    assert len(PAIRS) == 3
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
        {"grid_h": 5, "grid_w": 7, "rays": 5, "extra_blockers": 3},
        {"grid_h": 14, "grid_w": 18, "rays": 2, "extra_blockers": 1},
        {"grid_h": 7, "grid_w": 9, "rays": 3, "extra_blockers": 2},
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
        {"grid_w": 19},
        {"rays": 1},
        {"rays": 6},
        {"extra_blockers": 0},
        {"extra_blockers": 4},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"rays": "3"},
        {"extra_blockers": None},
    ],
)
def test_invalid_or_unknown_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_defaults_are_canonical_profiled_diverse_and_semantically_decisive(band):
    inputs = set()
    canonical_profiles = {(6, 8, 5), (7, 9, 5), (7, 9, 4)}
    exact = 0
    for index in range(96):
        grid = gen.generate(9_100 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert gen.strict_canonical_like(grid) == []
        assert teaching_errors(grid) == []
        assert grid == gen.generate(9_100 + index, index * 7 + 3, difficulty=band)
        inputs.add(frozen(grid))
        exact += profile(grid) in canonical_profiles
    assert len(inputs) >= 90
    assert exact >= 72


def test_replay_is_fresh_and_does_not_touch_global_random_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_canonical_shortcuts_fit_authority_but_every_generated_input_refutes_them():
    for name in ("skip_unit_gap", "last_blocker"):
        assert all(RIVALS[name](pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(64):
        grid = gen.generate(8_100 + index, index)
        official = rule_output(grid)
        for name, rival in RIVALS.items():
            assert rival(grid) != official, (index, name, grid)


def test_declared_semantic_contract_is_live_and_matches_independent_rivals():
    names = {"skip_unit_gap", "ignore_blocker", "last_blocker", "require_blocker"}
    witnesses = {"unit_gap", "trailing_background", "first_vs_last_blocker", "open_ray"}
    assert set(gen.SEMANTIC_RIVALS) == names
    assert set(gen.LESSON_COMPETITORS) == names
    assert set(gen.CANONICAL_SHORTCUTS) == {"skip_unit_gap", "last_blocker"}
    assert set(gen.SEMANTIC_WITNESSES) == witnesses
    assert gen.WITNESS_RIVALS == {
        "unit_gap": ["skip_unit_gap"],
        "trailing_background": ["ignore_blocker"],
        "first_vs_last_blocker": ["last_blocker"],
        "open_ray": ["require_blocker"],
    }
    for index in range(48):
        grid = gen.generate(20_000 + index, index)
        official = rule_output(grid)
        for witness in gen.SEMANTIC_WITNESSES.values():
            assert witness(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) == RIVALS[name](grid)
            assert rival(grid) != official


@pytest.mark.parametrize("grid", malformed_grids())
def test_malformed_or_non_lesson_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_minimal_structural_impostors():
    valid = gen.generate(11, 5, grid_h=7, grid_w=9, rays=3, extra_blockers=2)
    mutations = []

    blank = [[0 for _ in row] for row in valid]
    mutations.append(blank)

    multiple_seeds = deepcopy(valid)
    for row in multiple_seeds:
        seed = next((c for c, value in enumerate(row) if value not in (0, 5)), None)
        if seed is not None:
            target = next(c for c, value in enumerate(row) if value == 0 and c != seed)
            row[target] = 9 if row[seed] != 9 else 7
            break
    mutations.append(multiple_seeds)

    blocked_path = deepcopy(valid)
    for row in blocked_path:
        seeds = [c for c, value in enumerate(row) if value not in (0, 5)]
        right = [c for c, value in enumerate(row) if value == 5 and seeds and c > seeds[0]]
        if seeds and right and right[0] - seeds[0] >= 2:
            row[seeds[0] + 1] = 9 if row[seeds[0]] != 9 else 7
            break
    mutations.append(blocked_path)

    duplicate_color = deepcopy(valid)
    active = [(r, c) for r, row in enumerate(duplicate_color)
              for c, value in enumerate(row) if value not in (0, 5)]
    duplicate_color[active[1][0]][active[1][1]] = duplicate_color[active[0][0]][active[0][1]]
    mutations.append(duplicate_color)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation

@pytest.mark.parametrize("bad_index", [True, False, -1, 1.5, "2"])
def test_sample_index_must_be_a_nonnegative_strict_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad_index)


def test_default_profile_cycle_keeps_canonical_anchors_and_exercises_axis_endpoints():
    observed_rows = []
    for index in range(8):
        grid = gen.generate(0, index, difficulty="medium")
        observed_rows.append(observed(grid))
    assert min(row["grid_h"] for row in observed_rows) == 5
    assert max(row["grid_h"] for row in observed_rows) == 14
    assert min(row["grid_w"] for row in observed_rows) == 7
    assert max(row["grid_w"] for row in observed_rows) == 18
    assert sum(profile(gen.generate(0, index)) in {(6, 8, 5), (7, 9, 5), (7, 9, 4)}
               for index in range(8)) == 6
