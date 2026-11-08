"""Focused regression tests for the four-L-tromino packer."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "45e3c2212572"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_canonical_acceptance_and_python_rule_parity():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_vertical_rank_rival_fits_public_demos_but_not_held_out_pair():
    pairs = canonical_pairs(TASK_ID)
    assert all(
        GEN.rival_vertical_rank(pair["input"]) == pair["output"]
        for pair in pairs[:2]
    )
    assert GEN.rival_vertical_rank(pairs[2]["input"]) != pairs[2]["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_all_exact_override_boundaries_round_trip_in_every_band(band):
    cases = (
        {
            "grid_h": 11,
            "grid_w": 11,
            "layout_profile": "aligned",
            "palette_profile": "ascending",
        },
        {
            "grid_h": 15,
            "grid_w": 15,
            "layout_profile": "vertical_flip",
            "palette_profile": "descending",
        },
        {
            "grid_h": 11,
            "grid_w": 15,
            "layout_profile": "horizontal_flip",
            "palette_profile": "rotate_left",
        },
        {
            "grid_h": 15,
            "grid_w": 11,
            "layout_profile": "quarter_turn",
            "palette_profile": "swap_pairs",
        },
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(8100 + index, index, difficulty=band, **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_are_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, __typo_axis__=3)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 0, grid_h=10)
    with pytest.raises(ValueError, match="layout_profile"):
        GEN.generate(1, 0, layout_profile="not-a-profile")


def test_every_four_example_window_is_identifiable_and_refutes_vertical_rank():
    seed = 271828
    examples = [
        _pair(GEN.generate(seed, index, difficulty="medium"))
        for index in range(16)
    ]
    for start in range(12):
        demos = examples[start : start + GEN.EXAMPLES_NEEDED]
        query = examples[start + GEN.EXAMPLES_NEEDED]
        assert GEN.lesson_identifiable(demos, query) == []
        observed = [GEN.observe_overrides(pair["input"]) for pair in demos]
        assert {row["layout_profile"] for row in observed} == set(GEN.LAYOUT_PROFILES)
        assert {row["palette_profile"] for row in observed} == set(GEN.PALETTE_PROFILES)
        assert any(
            GEN.rival_vertical_rank(pair["input"]) != pair["output"]
            for pair in demos
        )


def test_vertical_flip_and_quarter_turn_are_direct_rival_killers():
    for layout in ("vertical_flip", "quarter_turn"):
        grid = GEN.generate(
            404,
            0,
            grid_h=13,
            grid_w=13,
            layout_profile=layout,
            palette_profile="ascending",
        )
        assert GEN.rule_mirror(grid) != GEN.rival_vertical_rank(grid)
        assert GEN.SEMANTIC_WITNESSES["vertical_rank_counterexample"](grid)


def test_every_targeted_mutation_fixture_is_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_recombining_four_valid_l_shapes_with_duplicate_orientation_is_rejected():
    valid = GEN.generate(
        991,
        0,
        grid_h=13,
        grid_w=13,
        layout_profile="aligned",
        palette_profile="ascending",
    )
    analysis = GEN._analyze_scene(valid)
    by_orientation = {
        component["orientation"]: component
        for component in analysis["components"]
    }
    mutated = copy.deepcopy(valid)
    victim = by_orientation["NE"]
    for row, col in victim["cells"]:
        mutated[row][col] = 0
    for dr, dc in GEN.SHAPES["SE"]:
        mutated[victim["top"] + dr][victim["left"] + dc] = victim["color"]
    errors = GEN.self_check(mutated)
    assert any("orientation exactly once" in error for error in errors)


def test_replay_is_deterministic_fresh_and_preserves_process_global_rng():
    random.seed(1234567)
    state = random.getstate()
    first = GEN.generate(12345, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(12345, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    third = GEN.generate(12345, 9, difficulty="hard")
    assert third == second
