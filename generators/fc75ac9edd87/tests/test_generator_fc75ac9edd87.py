"""Focused semantic regressions for generator fc75ac9edd87."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.fc75ac9edd87.generator"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_mirrored():
    assert GEN.RULE_HASH == "d042c4955bba"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    assert [sum(value == 1 for value in pair["input"][0]) for pair in pairs] == [1, 3, 4]
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_code_four_asymmetric_branch_is_generated_and_selects_correct_rank():
    for rank_sample in (3, 7):
        grid = GEN.generate(2026, rank_sample, difficulty="hard")
        facts = GEN.semantic_features(grid)
        assert facts["sym_code"] == 4
        assert facts["target_class"] == 0
        assert facts["rank"] in (1, 2)
        assert facts["n_match"] >= 2
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS["fixed_both_class"](grid)


def test_all_axis_boundaries_are_exact_and_observable_in_every_band():
    cases = [
        dict(sym_code=1, rank=1, grid_h=13, grid_w=16, n_match=2, n_distractor=1),
        dict(sym_code=4, rank=2, grid_h=20, grid_w=24, n_match=3, n_distractor=3),
    ]
    for band in ("easy", "medium", "hard"):
        for overrides in cases:
            grid = GEN.generate(77, 19, difficulty=band, **overrides)
            assert GEN.observe_overrides(grid) == overrides
            assert GEN.self_check(grid) == []


def test_eight_step_schedule_covers_every_code_rank_pair_and_every_window_teaches():
    pairs = []
    observed = set()
    for index in range(12):
        grid = GEN.generate(31337, index, difficulty="medium")
        facts = GEN.semantic_features(grid)
        observed.add((facts["sym_code"], facts["rank"]))
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert observed == {(code, rank) for code in range(1, 5) for rank in (1, 2)}
    for start in range(8):
        demos = pairs[start:start + GEN.EXAMPLES_NEEDED]
        query = pairs[start + GEN.EXAMPLES_NEEDED]
        assert GEN.lesson_identifiable(demos, query) == []


def test_named_rivals_are_actually_refuted_on_their_claimed_witnesses():
    grids = [GEN.generate(9001, index, difficulty="hard") for index in range(24)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for grid in firing:
            official = GEN.rule_mirror(grid)
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_self_check_rejects_declared_structural_impostors():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_default_draws_rebut_largest_object_and_bbox_fill_shortcuts():
    for band in ("easy", "medium", "hard"):
        for index in range(48):
            grid = GEN.generate(10000 + index, index, difficulty=band)
            facts = GEN.semantic_features(grid)
            assert facts["larger_wrong_class_distractor"]
            assert facts["winner_rectangular"] is False
            official = GEN.rule_mirror(grid)
            assert GEN.SEMANTIC_RIVALS["largest_body"](grid) != official
            assert GEN.SEMANTIC_RIVALS["bbox_fill"](grid) != official


def test_unknown_override_and_invalid_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, texture="warm")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(0, 0, difficulty="nightmare")


def test_determinism_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = GEN.generate(1234, 56, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 56, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(1234, 56, difficulty="hard") == second
