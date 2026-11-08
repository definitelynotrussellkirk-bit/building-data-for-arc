"""Task-local contract and semantic regressions for generator 44d20451ce17."""
from __future__ import annotations

from copy import deepcopy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


GEN = importlib.import_module("puzzle_generators.per_puzzle.44d20451ce17.generator")
ROOT = find_root(__file__)
TASK_ID = "44d20451ce17"
EXPECTED_AXES = {"grid_h", "grid_w", "n_ones", "scene_profile"}


def _pair(seed: int, sample_index: int, difficulty: str | None = None) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_schedule_metadata_avoids_an_unenumerated_period_claim() -> None:
    # Routine semantic-gate evidence samples schedule_profile directly; a positive
    # LESSON_SCHEDULE_PERIOD declaration is a separate fixed-seed census claim.
    # Exhaustive two-profile windows are covered below instead of overstating that
    # the routine gate enumerated a declared period.
    assert not hasattr(GEN, "LESSON_SCHEDULE_PERIOD")
    assert [GEN.schedule_profile(0, i) for i in range(4)] == [
        "canonical_scaffold",
        "counterexample",
        "canonical_scaffold",
        "counterexample",
    ]


def test_rule_pin_and_public_contract_are_explicit() -> None:
    assert GEN.RULE_HASH == "fc96c07b50d8"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.EXAMPLES_NEEDED == 3


def test_all_labeled_canonical_pairs_are_accepted_and_mirrored_exactly() -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical_scaffold", "counterexample"])
def test_exact_joint_overrides_are_constructive_and_observable(
    band: str | None, profile: str
) -> None:
    requested = {
        "grid_h": 5 if profile == "canonical_scaffold" else 10,
        "grid_w": 5,
        "n_ones": 4,
        "scene_profile": profile,
    }
    grid = GEN.generate(123, 17, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert sum(value == 1 for row in grid[:-1] for value in row) == 4


def test_retained_underproduction_counterexample_is_closed() -> None:
    grid = GEN.generate(
        123,
        0,
        grid_h=5,
        grid_w=5,
        n_ones=4,
        scene_profile="counterexample",
    )
    assert GEN.observe_overrides(grid)["n_ones"] == 4
    one_positions = [
        (r, c)
        for r, row in enumerate(grid[:-1])
        for c, value in enumerate(row)
        if value == 1
    ]
    assert len(one_positions) == 4
    assert len({c for _, c in one_positions}) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 4},
        {"grid_w": 11},
        {"n_ones": 0},
        {"n_ones": 5},
        {"scene_profile": "no_ones"},
        {"grid_h": True},
        {"grid_w": 5.0},
        {"n_ones": "4"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, "1", -1])
def test_sample_index_is_a_strict_nonnegative_integer(bad_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, bad_index)


def test_unknown_difficulty_is_rejected() -> None:
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_declared_shortcuts_fit_every_canonical_pair() -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    expected = {
        "bottom_five_only",
        "direct_five_support_only",
        "fixed_source_row_only",
        "lowest_one_only",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    assert set(GEN.SEMANTIC_RIVALS) == expected
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


def test_counterexample_profile_breaks_every_declared_shortcut() -> None:
    grid = GEN.generate(
        991,
        1,
        grid_h=5,
        grid_w=5,
        n_ones=4,
        scene_profile="counterexample",
    )
    truth = GEN.rule_mirror(grid)
    assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(deepcopy(grid)) != truth, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_three_demo_window_is_identifiable(
    band: str | None, start: int
) -> None:
    demos = [_pair(7331, start + offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
    query = _pair(7331, start + GEN.EXAMPLES_NEEDED, band)
    assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), (
            band,
            start,
            name,
        )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_the_exact_canonical_profile_in_every_band(band: str) -> None:
    grids = [GEN.generate(8801, index, difficulty=band) for index in range(20)]
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert (5, 5, 3) in profiles
    assert {GEN.schedule_profile(8801, index, band) for index in range(20)} == set(
        GEN.SCHEDULE_PROFILES
    )
    assert all(GEN.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[1] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(4)] + [[1] * 5],
        [[0] * 5 for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_or_rule_hiding_impostors(grid) -> None:
    assert GEN.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(1941)
    state = random.getstate()
    first = GEN.generate(2026, 11, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(2026, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state == after
