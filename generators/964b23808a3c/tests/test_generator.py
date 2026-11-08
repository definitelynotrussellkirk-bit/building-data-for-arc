"""Regression contract for the repaired 964b23808a3c input generator.

The Python oracle below is deliberately independent of generator.rule_mirror.
Canonical answers are authoring data and must stay closed during solve episodes.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "964b23808a3c"
ROOT = find_root(__file__)
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def oracle(grid):
    """Independent transcription of the selected Racket rule."""
    out = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for col in range(width):
        marks = [row for row in range(height) if grid[row][col] != 0]
        if not marks or grid[marks[-1]][col] != 5:
            continue
        previous = -1
        for row in marks:
            color = grid[row][col]
            for fill_row in range(previous + 1, row + 1):
                out[fill_row][col] = color
            previous = row
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def all_competitors():
    declared = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        rules = getattr(gen, namespace)
        assert isinstance(rules, dict) and rules
        for name, rule in rules.items():
            assert isinstance(name, str) and callable(rule)
            declared.setdefault(name, rule)
    return declared


def test_canonical_pairs_are_owned_and_match_independent_oracle():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        expected = oracle(pair["input"])
        assert expected == pair["output"], (pair["split"], pair["pair_index"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == expected


def test_rule_hash_and_executable_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "c7e69da25375"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.SCHEDULE_PROFILES) == {
        "minimal", "clean", "noisy", "dense"
    }
    assert callable(gen.schedule_profile)
    assert callable(gen.lesson_identifiable)
    assert callable(gen.observe_overrides)
    assert all_competitors()
    witnesses = gen.SEMANTIC_WITNESSES
    assert isinstance(witnesses, dict) and witnesses
    assert set(gen.WITNESS_RIVALS) <= set(witnesses)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 7,
            "grid_w": 7,
            "n_targets": 3,
            "n_marks_per_target": 5,
            "distractor_mode": "mixed",
            "terminator_position": "floating",
        },
        {
            "grid_h": 20,
            "grid_w": 20,
            "n_targets": 1,
            "n_marks_per_target": 2,
            "distractor_mode": "none",
            "terminator_position": "bottom",
        },
    ],
)
def test_joint_exact_overrides_are_observable(difficulty, requested):
    grid = gen.generate(911, 37, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == oracle(grid)
    assert gen.rule_mirror(grid) != grid


def test_invalid_calls_are_rejected_instead_of_silently_coerced():
    with pytest.raises((TypeError, ValueError), match="unknown"):
        gen.generate(1, 0, typo_axis=1)
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises((TypeError, ValueError), match="integer|bool"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="integer"):
        gen.generate(1, 0, n_targets="2")


EXPECTED_PROFILES = {
    0: ((7, 7, 3), {"grid_h": 7, "grid_w": 7, "n_targets": 1,
                     "n_marks_per_target": 2, "distractor_mode": "none",
                     "terminator_position": "bottom"}, "minimal"),
    1: ((12, 12, 7), {"grid_h": 12, "grid_w": 12, "n_targets": 2,
                       "n_marks_per_target": 4, "distractor_mode": "none",
                       "terminator_position": "bottom"}, "clean"),
    2: ((13, 13, 9), {"grid_h": 13, "grid_w": 13, "n_targets": 2,
                       "n_marks_per_target": 3, "distractor_mode": "mixed",
                       "terminator_position": "floating"}, "noisy"),
    3: ((17, 17, 10), {"grid_h": 17, "grid_w": 17, "n_targets": 3,
                        "n_marks_per_target": 5, "distractor_mode": "mixed",
                        "terminator_position": "floating"}, "dense"),
}


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(4))
def test_default_schedule_hits_each_canonical_profile_in_every_band(seed, difficulty):
    for index, (expected_profile, expected_axes, expected_schedule) in EXPECTED_PROFILES.items():
        grid = gen.generate(seed, index, difficulty=difficulty)
        assert profile(grid) == expected_profile
        assert gen.observe_overrides(grid) == expected_axes
        assert gen.schedule_profile(seed, index, difficulty) == expected_schedule
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == oracle(grid)


def test_declared_canonical_shortcuts_really_fit_all_canonical_labels():
    shortcuts = gen.CANONICAL_SHORTCUTS
    assert set(shortcuts) == {
        "any_column_containing_5",
        "bottom_row_5_only",
        "extend_5_below_terminator",
    }
    for name, rule in shortcuts.items():
        for pair in PAIRS:
            assert rule(pair["input"]) == pair["output"], (
                name, pair["split"], pair["pair_index"]
            )


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(8))
def test_noisy_profiles_refute_every_declared_competitor(seed, difficulty):
    competitors = all_competitors()
    for index in (2, 3):
        grid = gen.generate(seed, index, difficulty=difficulty)
        expected = oracle(grid)
        fired = {name for name, predicate in gen.SEMANTIC_WITNESSES.items()
                 if predicate(grid)}
        assert {"distractor_column", "internal_five_distractor",
                "floating_terminator", "top_gap", "current_marker_color"} <= fired
        for name, rule in competitors.items():
            assert rule(grid) != expected, (seed, difficulty, index, name)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(6))
def test_every_four_pair_window_is_identifiable_under_each_query_rotation(seed, difficulty):
    competitors = all_competitors()
    grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(12)]
    for start in range(9):
        window = grids[start:start + 4]
        pairs = [{"input": grid, "output": oracle(grid)} for grid in window]
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rule in competitors.items():
                if all(rule(pair["input"]) == pair["output"] for pair in demos):
                    assert rule(query["input"]) == query["output"], (
                        seed, difficulty, start, query_index, name
                    )


def test_generation_is_deterministic_and_returns_fresh_grids():
    first = gen.generate(73, 11, difficulty="hard")
    second = gen.generate(73, 11, difficulty="hard")
    assert first == second
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [[]],
        [[0, 0], [0]],
        [[0, True], [0, 5]],
        [[0, 10], [0, 5]],
        [[0, 0], [0, 0]],
        [[5, 0], [5, 0]],
    ],
)
def test_self_check_rejects_malformed_or_degenerate_inputs(bad):
    assert gen.self_check(bad)


def test_default_schedule_decouples_target_count_from_mark_count():
    observed = [gen.observe_overrides(gen.generate(41, index)) for index in range(4)]
    mark_counts_for_two_targets = {
        item["n_marks_per_target"] for item in observed if item["n_targets"] == 2
    }
    assert len(mark_counts_for_two_targets) >= 2


def test_difficulty_band_changes_geometry_without_changing_profile():
    grids = [gen.generate(2026, 3, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) >= 2
    assert len({profile(grid) for grid in grids}) == 1
