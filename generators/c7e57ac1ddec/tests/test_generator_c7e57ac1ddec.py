"""Focused regression tests for generator c7e57ac1ddec."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.c7e57ac1ddec import generator as gen


TASK_ID = "c7e57ac1ddec"


def _canonical_row():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def test_canonical_inputs_and_outputs_match_rule_mirror():
    row = _canonical_row()
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_are_structural_and_semantic(difficulty):
    for seed in range(24):
        grid = gen.generate(seed, seed + 17, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        observed = gen.observe_overrides(grid)
        assert 4 <= observed["n_targets"] <= 6
        assert 1 <= observed["n_long_gaps"] <= 3
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != gen.rule_mirror(grid)


def test_override_boundaries_are_exact_and_observable():
    cases = (
        {"grid_h": 7, "grid_w": 10, "n_targets": 4, "n_long_gaps": 1},
        {"grid_h": 12, "grid_w": 14, "n_targets": 8, "n_long_gaps": 3},
        {"grid_h": 7, "grid_w": 14, "n_targets": 8, "n_long_gaps": 1},
        {"grid_h": 12, "grid_w": 10, "n_targets": 4, "n_long_gaps": 3},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, bogus_axis=3)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError, match="n_targets"):
        gen.generate(1, 0, n_targets=9)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(44, 9, difficulty="medium")
    after = random.getstate()
    assert before == after

    second = gen.generate(44, 9, difficulty="medium")
    assert first == second
    first[0][0] = 9
    third = gen.generate(44, 9, difficulty="medium")
    assert third == second
    assert first is not second and second is not third
    assert all(a is not b for a, b in zip(second, third))


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(17, 4, difficulty="easy")

    wrong_color = [row[:] for row in valid]
    wrong_color[0][0] = 5
    assert any("colors" in message for message in gen.self_check(wrong_color))

    no_targets = [[0 for _ in row] for row in valid]
    no_targets[0][0] = no_targets[2][0] = 2
    assert any("horizontal" in message for message in gen.self_check(no_targets))

    no_long_gap = [row[:] for row in valid]
    analysis = gen._analysis_or_raise(no_long_gap)
    for row, left, right, _ in analysis["long_gaps"]:
        for col in range(left + 1, right):
            no_long_gap[row][col] = 2
    assert any("longer" in message for message in gen.self_check(no_long_gap))

    no_vertical_distractor = [[0] * 10 for _ in range(7)]
    no_vertical_distractor[0] = [2, 2, 0, 2, 0, 2, 0, 2, 0, 2]
    no_vertical_distractor[1][0:4] = [2, 0, 0, 2]
    assert any("vertical" in message for message in gen.self_check(no_vertical_distractor))


def test_materialized_lesson_refutes_named_competitors():
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(700, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(700, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for competitor in gen.LESSON_COMPETITORS.values():
        assert any(competitor(pair["input"]) != pair["output"] for pair in demos)
