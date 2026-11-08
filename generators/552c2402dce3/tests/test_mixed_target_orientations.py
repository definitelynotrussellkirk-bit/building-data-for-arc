"""Regression coverage for per-target missing-corner teaching support."""
from __future__ import annotations

import importlib

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.552c2402dce3.generator")


def _broadcast_first_orientation(grid):
    """Canonical-train-fitting rival: reuse the first target's orientation."""
    targets = gen._target_windows(grid)
    assert targets
    return gen._fill_targets(grid, allowed_missing={targets[0]["missing"]})


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_generated_input_refutes_first_orientation_broadcast(difficulty) -> None:
    for seed in range(4):
        for sample_index in range(8):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            orientations = {target["missing"] for target in gen._target_windows(grid)}
            assert len(orientations) >= 2, (difficulty, seed, sample_index, orientations)
            assert _broadcast_first_orientation(grid) != gen._solve_true_local_rule(grid)


def test_first_orientation_broadcast_is_a_declared_lesson_competitor() -> None:
    assert "broadcast_first_orientation" in gen.LESSON_COMPETITORS


def _pair(grid):
    return {"input": grid, "output": gen._solve_true_local_rule(grid)}


def test_every_single_query_rotation_remains_identifiable() -> None:
    for seed in range(4):
        for start in range(4):
            pairs = [_pair(gen.generate(seed, start + offset)) for offset in range(5)]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    seed,
                    start,
                    query_index,
                    gen.lesson_identifiable(demos, query),
                )
