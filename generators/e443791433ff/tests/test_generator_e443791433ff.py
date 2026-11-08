from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.e443791433ff import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


def test_rule_hash_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "d9de6efb6a97"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_regression_dead_and_unknown_overrides_reject_loudly() -> None:
    # The assigned baseline accepted both of these without consuming them.
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", palette_kind="warm")
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", __override_contract_unknown_axis__=1)


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = [
        {"grid_h": 8, "grid_w": 10, "n_sources": 6, "n_decoys": 1},
        {"grid_h": 10, "grid_w": 12, "n_sources": 12, "n_decoys": 4},
    ]
    for band in ("easy", "medium", "hard"):
        for sample_index, case in enumerate(cases):
            for seed in range(12):
                grid = gen.generate(seed, sample_index, difficulty=band, **case)
                assert gen.observe_overrides(grid) == case
                assert gen.self_check(grid) == []
                assert gen.rule_mirror(grid) != grid


def test_two_consecutive_demos_cover_conditional_shortcut_killers() -> None:
    for start in range(20):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(500 + offset, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query = {
            "input": gen.generate(700, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        }
        assert gen.lesson_identifiable(demos, query) == []
        signatures = [gen.profile_signature(pair["input"]) for pair in demos]
        assert any(item["blocked_by_three"] > 0 for item in signatures)
        assert any(item["blocked_by_three"] == 0 for item in signatures)
        assert all(item["blocked_by_two"] > 0 for item in signatures)
        assert all(item["unrelated_twos"] > 0 for item in signatures)


def test_mutation_fixtures_reject_semantic_impostors() -> None:
    fixtures = dict(gen.mutation_fixtures())
    assert len(fixtures) >= 6
    expected = {
        "no_sources": "color-3 sources",
        "no_color2_blocker": "blocked by a color-2",
        "no_castable_source": "empty down-right target",
        "gray_in_input": "unexpected colors",
        "border_source": "in-bounds down-right",
        "unexpected_color": "unexpected colors",
    }
    for name, fragment in expected.items():
        errors = gen.self_check(fixtures[name])
        assert errors, name
        assert any(fragment in error for error in errors), (name, errors)


def test_strict_linked_semantic_census_and_disjoint_stability() -> None:
    for seed_base in (10_000, 30_000):
        for band in ("easy", "medium", "hard"):
            signatures = []
            for index in range(200):
                grid = gen.generate(seed_base + index, index, difficulty=band)
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                signatures.append(gen.profile_signature(grid))
            assert all(item["casting"] > 0 for item in signatures)
            assert all(item["blocked_by_two"] > 0 for item in signatures)
            assert all(item["unrelated_twos"] > 0 for item in signatures)
            assert 80 <= sum(item["blocked_by_three"] > 0 for item in signatures) <= 120
            assert len({(item["height"], item["width"]) for item in signatures}) >= 3
            assert len({item["n_sources"] for item in signatures}) >= 3
            assert len({item["n_decoys"] for item in signatures}) >= 2


def test_replay_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    snapshot = copy.deepcopy(first)
    second = gen.generate(77, 9, difficulty="hard")
    assert first == second == snapshot
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    _ = gen.rule_mirror(first)
    assert first == snapshot
    first[0][0] = 9 if first[0][0] != 9 else 0
    third = gen.generate(77, 9, difficulty="hard")
    assert third == second
