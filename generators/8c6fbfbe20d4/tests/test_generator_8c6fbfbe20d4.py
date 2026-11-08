"""Focused regressions for the 8c6fbfbe20d4 nonzero-list recolor generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.8c6fbfbe20d4.generator"
)


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned_and_solved() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "27daa6126c50"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        before = copy.deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_override_boundaries_and_unknown_axis_rejection() -> None:
    grid = gen.generate(
        41,
        7,
        difficulty="easy",
        N=4,
        target_n=5,
        body_h=10,
        grid_w=5,
        n_unmapped=4,
    )
    assert gen.observe_overrides(grid) == {
        "N": 4,
        "target_n": 5,
        "body_h": 10,
        "grid_w": 5,
        "n_unmapped": 4,
    }
    assert gen.self_check(grid) == []

    low = gen.generate(
        42,
        6,
        difficulty="hard",
        N=2,
        target_n=2,
        body_h=3,
        grid_w=5,
        n_unmapped=0,
    )
    assert gen.observe_overrides(low) == {
        "N": 2,
        "target_n": 2,
        "body_h": 3,
        "grid_w": 5,
        "n_unmapped": 0,
    }

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)


def test_four_demo_windows_refute_every_named_competitor() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [
                _pair(1000 + start, start + offset, difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(2000 + start, start + gen.EXAMPLES_NEEDED, difficulty)
            assert gen.lesson_identifiable(demos, query) == []
            profiles = {
                gen.schedule_profile(0, start + offset, difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            }
            assert profiles == set(gen.SCHEDULE_PROFILES)
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                )


def test_generated_curriculum_refutes_canonical_erase_unmapped_shortcut() -> None:
    # Canonical examples never contain unmapped body values, so this wrong rule
    # is observationally equivalent there and must be killed by generated data.
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen.CANONICAL_SHORTCUTS["erase_unmapped_body"](
            pair["input"]
        ) == pair["output"]

    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(77, 2, difficulty=difficulty)
        assert gen.SEMANTIC_WITNESSES["unpaired_source_is_preserved"](grid)
        assert gen.SEMANTIC_RIVALS["erase_unmapped_body"](grid) != gen.rule_mirror(grid)

        grid = gen.generate(78, 1, difficulty=difficulty)
        assert gen.SEMANTIC_WITNESSES["unmapped_body_value_is_preserved"](grid)
        assert gen.SEMANTIC_RIVALS["erase_unmapped_body"](grid) != gen.rule_mirror(grid)


def test_self_check_rejects_structural_impostors() -> None:
    base = gen.generate(1234, 1, difficulty="medium")
    assert gen.self_check(base) == []

    duplicate_source = copy.deepcopy(base)
    src_cols = [i for i, value in enumerate(duplicate_source[0]) if value]
    duplicate_source[0][src_cols[1]] = duplicate_source[0][src_cols[0]]
    assert any("source colors" in error for error in gen.self_check(duplicate_source))

    overlap = copy.deepcopy(base)
    tgt_col = next(i for i, value in enumerate(overlap[1]) if value)
    overlap[1][tgt_col] = next(value for value in overlap[0] if value)
    assert any("disjoint" in error for error in gen.self_check(overlap))

    missing_source = copy.deepcopy(base)
    absent = next(value for value in missing_source[0] if value)
    replacement = next(value for value in missing_source[0] if value and value != absent)
    for row in range(2, len(missing_source)):
        for col in range(len(missing_source[0])):
            if missing_source[row][col] == absent:
                missing_source[row][col] = replacement
    assert any("missing" in error for error in gen.self_check(missing_source))

    too_many_unmapped = copy.deepcopy(base)
    source_set = {value for value in too_many_unmapped[0] if value}
    outside = next(color for color in range(1, 10) if color not in source_set)
    placed = 0
    for row in range(2, len(too_many_unmapped)):
        for col in range(len(too_many_unmapped[0])):
            if too_many_unmapped[row][col] == 0 and placed < 5:
                too_many_unmapped[row][col] = outside
                placed += 1
    assert placed == 5
    assert any("at most 4" in error for error in gen.self_check(too_many_unmapped))


def test_determinism_fresh_returns_and_global_rng_is_untouched() -> None:
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(91, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(91, 2, difficulty="hard")
    assert first == second
    assert first is not second

    first[2][0] = 99
    third = gen.generate(91, 2, difficulty="hard")
    assert third == second

    before = copy.deepcopy(third)
    _ = gen.rule_mirror(third)
    assert third == before
