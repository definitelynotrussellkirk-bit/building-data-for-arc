"""Focused regression tests for the 4c9d99d61804 portal-path generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.4c9d99d61804.generator"
)
TASK_ID = "4c9d99d61804"


def _episode(seed: int, start_index: int, difficulty: str):
    demos = []
    for index in range(start_index, start_index + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.oracle_output(grid)})
    query_grid = GEN.generate(
        seed, start_index + GEN.EXAMPLES_NEEDED, difficulty=difficulty
    )
    return demos, {"input": query_grid, "output": GEN.oracle_output(query_grid)}


def test_rule_pin_all_canonical_pairs_and_canonical_ambiguity():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "bd90e027e0bf"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4

    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original
        # These are genuine shortcuts: all four fit every supplied example.
        for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
            assert shortcut(pair["input"]) == pair["output"], name


def test_five_profile_schedule_kills_every_rival_in_every_sliding_window():
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for start_index in range(10):
            demos, query = _episode(1701, start_index, difficulty)
            profiles = {
                GEN.schedule_profile(1701, index, difficulty)
                for index in range(start_index, start_index + GEN.EXAMPLES_NEEDED)
            }
            assert profiles == expected_profiles
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), name


def test_each_profile_is_a_positive_semantic_discriminator():
    grids = {
        GEN.schedule_profile(77, index, "medium"): GEN.generate(
            77, index, difficulty="medium"
        )
        for index in range(GEN.EXAMPLES_NEEDED)
    }
    assert set(grids) == set(GEN.SCHEDULE_PROFILES)
    for name, grid in grids.items():
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN._profile_matches(grid, name)

    assert GEN._plain_bfs_output(grids["portal_shortcut"]) != GEN.oracle_output(
        grids["portal_shortcut"]
    )
    assert GEN._forced_portal_output(grids["portal_distractor"]) != GEN.oracle_output(
        grids["portal_distractor"]
    )
    assert GEN._output_for_order(
        grids["up_before_down_tie"], "DULR"
    ) != GEN.oracle_output(grids["up_before_down_tie"])
    assert GEN._output_for_order(
        grids["down_before_left_tie"], "ULDR"
    ) != GEN.oracle_output(grids["down_before_left_tie"])
    assert GEN._output_for_order(
        grids["left_before_right_tie"], "UDRL"
    ) != GEN.oracle_output(grids["left_before_right_tie"])


def test_exact_override_boundaries_are_observable_in_every_band():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for height in (7, 8, 9):
            for width in (10, 11, 12):
                for portal_color in (7, 8, 9):
                    requested = {
                        "grid_h": height,
                        "grid_w": width,
                        "portal_color": portal_color,
                    }
                    grid = GEN.generate(
                        9000 + case,
                        case % GEN.EXAMPLES_NEEDED,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert GEN.self_check(
                        grid, difficulty=difficulty, meta={"overrides": requested}
                    ) == []
                    assert GEN.observe_overrides(grid) == requested
                    case += 1

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, definitely_unknown_axis=7)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_structural_mutation_fixtures_are_rejected():
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 7
    assert "unpaired_replacement_color" in fixtures
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name

    # The negative recombination is distribution-invalid even though the
    # diagnostic Python oracle remains total and returns a same-shaped grid.
    malformed = fixtures["unpaired_replacement_color"]
    output = GEN.oracle_output(malformed)
    assert len(output) == len(malformed)
    assert all(len(out_row) == len(in_row) for out_row, in_row in zip(output, malformed))


def test_replay_is_fresh_deterministic_and_process_rng_pure():
    random.seed(20260816)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
