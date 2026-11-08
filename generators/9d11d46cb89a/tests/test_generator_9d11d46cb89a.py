"""Regression and curriculum tests for the 9d11d46cb89a room lookup generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)
from scripts.rule_smoke import rule_application

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.9d11d46cb89a.generator"
)
TASK_ID = "9d11d46cb89a"


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_metadata_hash_and_canonical_pairs() -> None:
    assert GEN.VERSION == "3.2.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "3c5efa300447"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    assert {GEN.semantic_observables(pair["input"])["query_match"] for pair in pairs} == {
        "key1",
        "key2",
    }
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_axes_are_observable_for_every_declared_value() -> None:
    cases = []
    for room_profile in GEN.ROOM_PROFILES:
        for wall_color in GEN.WALL_COLORS:
            cases.append({"room_profile": room_profile, "wall_color": wall_color})
    for query_match in GEN.QUERY_MATCHES:
        for key_discriminator in GEN.KEY_DISCRIMINATORS:
            for motif_size in GEN.MOTIF_SIZES:
                cases.append(
                    {
                        "query_match": query_match,
                        "key_discriminator": key_discriminator,
                        "motif_size": motif_size,
                    }
                )

    for index, overrides in enumerate(cases):
        grid = GEN.generate(1000 + index, index, difficulty="medium", **overrides)
        observed = GEN.observe_overrides(grid)
        for axis, value in overrides.items():
            assert observed[axis] == value
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis="shape")


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(24680)
    state = random.getstate()
    first = GEN.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[1][1] = 0
    assert GEN.generate(77, 9, difficulty="hard") == second


def test_four_slot_schedule_is_identifiable_from_every_window_start() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            demos = [
                _pair(4000 + start, start + offset, difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            query = _pair(
                4000 + start,
                start + GEN.EXAMPLES_NEEDED,
                difficulty,
            )
            assert GEN.lesson_identifiable(demos, query) == []
            facts = [GEN.semantic_observables(pair["input"]) for pair in demos]
            assert {fact["query_match"] for fact in facts} == set(GEN.QUERY_MATCHES)
            assert {fact["key_discriminator"] for fact in facts} == set(
                GEN.KEY_DISCRIMINATORS
            )
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                )


def test_declared_witnesses_fire_in_every_band_and_kill_named_rivals() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(8000 + index, index, difficulty=difficulty) for index in range(40)]
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (difficulty, witness_name)
            for grid in firing[:12]:
                official = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != official
                    for rival_name in GEN.WITNESS_RIVALS[witness_name]
                )


def test_strict_linked_census_is_complete_and_varied() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(12000 + index, index, difficulty=difficulty)
            for index in range(200)
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert all(len(grid) <= 30 and len(grid[0]) <= 30 for grid in grids)
        assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 190
        branch_counts = {
            branch: sum(
                GEN.semantic_observables(grid)["query_match"] == branch
                for grid in grids
            )
            for branch in GEN.QUERY_MATCHES
        }
        assert all(count > 0 for count in branch_counts.values())


def test_task_specific_mutation_fixtures_are_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_negative_recombination_is_rejected_but_oracle_still_executes() -> None:
    grid = GEN.generate(991, 3, difficulty="medium")
    facts = GEN.semantic_observables(grid)
    recombined = copy.deepcopy(grid)
    query = facts["motifs"][4]
    absent_color = next(
        color
        for color in GEN.CONTENT_COLORS
        if color not in {value for row in grid for value in row}
    )
    query_left = GEN._room_left(4, facts["room_w"])
    cell = next(iter(query))
    recombined[1 + cell[0]][query_left + cell[1]] = absent_color
    assert GEN.self_check(recombined)

    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        output = bridge.eval_text(
            rule_application(canonical_rule_source(TASK_ID), recombined)
        )
        assert isinstance(output, list) and output
    finally:
        bridge.shutdown()
