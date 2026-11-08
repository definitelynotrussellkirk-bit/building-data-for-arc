"""Focused regression tests for generator b46e718788e1."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_rule_hash


TASK_ID = "b46e718788e1"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _all_canonical_pairs():
    row = _canonical_row()
    return [*row["train"], row["test"]]


def test_rule_hash_matches_canonical_authority():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)


def test_self_check_accepts_canonical_and_python_mirror_matches_outputs():
    for pair in _all_canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_boundary_overrides_round_trip_and_unknown_keys_reject():
    cases = [
        dict(grid_h=5, grid_w=5, border_objects=1, interior_objects=1),
        dict(grid_h=5, grid_w=5, border_objects=2, interior_objects=2),
        dict(grid_h=10, grid_w=11, border_objects=2, interior_objects=2),
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(701 + index, index, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_ordinary_draws_always_demonstrate_keep_and_erase_branches():
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            grid = GEN.generate(seed, seed * 13 + 5, difficulty=band)
            out = GEN.rule_mirror(grid)
            assert out != grid
            assert any(value != 0 for row in out for value in row)
            profile = GEN.semantic_profile(grid)
            assert profile["border_objects"] >= 1
            assert profile["interior_objects"] >= 1
            assert profile["changed_cell_count"] >= 2


def test_four_sample_schedule_kills_training_shortcuts():
    for start in range(8):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(9001, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(9001, start + GEN.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []
        witness_names = {
            name
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if any(predicate(pair["input"]) for pair in demos)
        }
        assert "edge_only_border_component" in witness_names
        assert "multiple_kept_components" in witness_names
        assert "shared_color_opposite_fate" in witness_names


def test_shared_color_witness_refutes_global_border_color_shortcut():
    found = False
    for sample_index in range(12):
        grid = GEN.generate(1212, sample_index, difficulty="easy")
        if GEN.SEMANTIC_WITNESSES["shared_color_opposite_fate"](grid):
            found = True
            assert GEN.CANONICAL_SHORTCUTS[
                "keep_every_component_of_a_border_color"
            ](grid) != GEN.rule_mirror(grid)
    assert found


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_untouched():
    random.seed(424242)
    before = random.getstate()
    first = GEN.generate(77, 31, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(77, 31, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
