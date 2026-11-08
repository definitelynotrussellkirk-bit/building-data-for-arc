from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "85dcd5c922b9"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned_and_solved():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "6ab6552b1d13"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(original) == []
        assert GEN.strict_canonical_like(original) == []
        assert GEN.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_profile_schedule_is_canonical_and_repeats_after_three_demos():
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(9):
            grid = GEN.generate(1000 + index, index, difficulty=band)
            facts = GEN._analysis(grid)
            assert facts["profile"] in GEN.CANONICAL_PROFILES
            assert GEN.self_check(grid, difficulty=band) == []
            assert GEN.strict_canonical_like(grid) == []
            profiles.append(facts["profile"])
            for witness in GEN.SEMANTIC_WITNESSES.values():
                assert witness(grid)
        assert profiles[:3] == list(GEN.PROFILE_CYCLE)
        assert profiles[3:6] == profiles[:3]
        assert profiles[6:9] == profiles[:3]


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    cases = (
        {"first_row_load": 2},
        {"first_row_load": 3},
        {"blank_row": "none"},
        {"blank_row": "last"},
        {"first_row_load": 2, "blank_row": "none"},
        {"first_row_load": 3, "blank_row": "last"},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(2000 + index, index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            for key, value in case.items():
                assert observed[key] == value
            assert GEN.self_check(grid, difficulty=band, meta={"overrides": case}) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="silent bugs are not allowed")


def test_every_three_demo_sliding_window_identifies_the_next_query():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            episode = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(3000 + start, sample_index, difficulty=band)
                episode.append(_pair(grid))
            assert GEN.lesson_identifiable(
                episode[: GEN.EXAMPLES_NEEDED], episode[-1]
            ) == []


def test_self_check_rejects_declared_impostors_and_old_degenerates():
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_order_is_preserved_not_sorted_reversed_or_left_packed():
    grid = GEN.generate(4040, 1, difficulty="hard", first_row_load=3, blank_row="none")
    official = GEN.rule_mirror(grid)
    assert official != grid
    assert GEN._left_pack(grid) != official
    assert GEN._reverse_right_pack(grid) != official
    assert GEN._sorted_right_pack(grid, reverse=False) != official
    assert GEN._sorted_right_pack(grid, reverse=True) != official
    assert GEN._one_step_right(grid) != official


def test_deterministic_fresh_returns_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    intervening = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert intervening != first
    baseline_sha = _sha(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _sha(GEN.generate(77, 19, difficulty="hard")) == baseline_sha
