from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "834177c803c3"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair_rows():
    return canonical_pairs(TASK_ID)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_match_the_authority_contract():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = _pair_rows()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_are_observable_and_structurally_valid():
    cases = [
        {"grid_h": 3, "panel_w": 3, "n_right_colors": 6},
        {"grid_h": 6, "panel_w": 6, "n_right_colors": 9},
        {"grid_h": 3, "panel_w": 6, "n_right_colors": 9},
        {"grid_h": 6, "panel_w": 3, "n_right_colors": 6},
    ]
    for difficulty in ("easy", "medium", "hard"):
        for seed, requested in enumerate(cases):
            grid = gen.generate(seed, 3, difficulty=difficulty, **requested)
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid, meta={"overrides": requested}) == []


def test_unknown_and_out_of_domain_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)
    for key, value in (
        ("grid_h", 2),
        ("grid_h", 7),
        ("panel_w", 2),
        ("panel_w", 7),
        ("n_right_colors", 5),
        ("n_right_colors", 10),
    ):
        with pytest.raises(ValueError, match="outside"):
            gen.generate(0, 3, **{key: value})


def test_determinism_fresh_returns_and_process_global_rng_purity():
    random.seed(918273)
    state = random.getstate()
    first = gen.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(11, 0, difficulty="medium")
    panel_w = (len(valid[0]) - 1) // 2

    broken_separator = copy.deepcopy(valid)
    broken_separator[0][panel_w] = 7
    assert any("separator" in reason for reason in gen.self_check(broken_separator))

    nonbinary_mask = copy.deepcopy(valid)
    nonbinary_mask[0][0] = 2
    assert any("binary" in reason for reason in gen.self_check(nonbinary_mask))

    zero_payload = copy.deepcopy(valid)
    zero_payload[0][panel_w + 1] = 0
    assert any("nonzero" in reason for reason in gen.self_check(zero_payload))

    uniform_mask_row = copy.deepcopy(valid)
    uniform_mask_row[0][:panel_w] = [1] * panel_w
    assert any("both selected" in reason for reason in gen.self_check(uniform_mask_row))

    even_width = copy.deepcopy(valid)
    for row in even_width:
        row.pop()
    assert any("odd" in reason for reason in gen.self_check(even_width))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in reason for reason in gen.self_check(ragged))


def test_every_ordinary_schedule_slot_has_decisive_witnesses_and_rival_separation():
    for difficulty in ("easy", "medium", "hard"):
        strict_hits = 0
        for sample_index in range(16):
            grid = gen.generate(31337, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == gen._scheduled_defaults(
                31337, sample_index, difficulty
            )
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (difficulty, sample_index, witness_name)
            truth = gen.rule_mirror(grid)
            for rival_name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (difficulty, sample_index, rival_name)
            strict_hits += not gen.strict_canonical_like(grid)
        assert strict_hits == 12


def test_every_sliding_two_demo_window_identifies_the_mask_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(20):
            demos = [
                _pair(gen.generate(1000 + start, sample_index, difficulty=difficulty))
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen.generate(
                    1000 + start,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_compact_explicit_override_is_lawful_without_overclaiming_curriculum_support():
    requested = {"grid_h": 3, "panel_w": 3, "n_right_colors": 9}
    grid = gen.generate(5150, 3, difficulty="hard", **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert len({value for row in grid for value in row[4:]}) == 9
