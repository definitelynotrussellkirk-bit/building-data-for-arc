from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "32a376372541"
GEN_PATH = Path("puzzle_generators/per_puzzle") / TASK_ID / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    gen = _load()
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_unknown_override_rejects_and_all_profiles_round_trip():
    gen = _load()
    with pytest.raises(TypeError):
        gen.generate(11, 0, difficulty="easy", typo_axis=True)
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(500 + index, index, scene_profile=profile)
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_every_two_demo_window_contains_one_way_decoy_and_is_identifiable():
    gen = _load()
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for index in range(8):
            grid = gen.generate(701, index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(6):
            demos = pairs[start : start + 2]
            query = pairs[start + 2]
            assert any(gen._witness_one_way_decoy(pair["input"]) for pair in demos)
            assert gen.lesson_identifiable(demos, query) == []


def test_right_decoy_kills_bidirectional_shortcut_but_clean_profile_does_not():
    gen = _load()
    clean = gen.generate(31, 0, scene_profile="e6x8_c4_p4_clean")
    decoy = gen.generate(31, 1, scene_profile="e6x8_c6_p4_decoy")
    assert gen._rival_bidirectional_mirror(clean) == gen.rule_mirror(clean)
    assert gen._rival_bidirectional_mirror(decoy) != gen.rule_mirror(decoy)


def test_self_check_rejects_four_structural_impostors():
    gen = _load()
    good = gen.generate(91, 0, scene_profile="m7x10_c5_p5_clean")

    odd_width = [row[:-1] for row in good]
    assert any("odd" in reason for reason in gen.self_check(odd_width))

    no_source = [[0 for _ in row] for row in good]
    assert gen.self_check(no_source)

    one_row = [[0 for _ in row] for row in good]
    for col, color in enumerate((1, 2, 3)):
        one_row[0][col] = color
    assert any("three rows" in reason for reason in gen.self_check(one_row))

    collision = copy.deepcopy(good)
    left = next((r, c) for r, row in enumerate(good) for c, value in enumerate(row[: len(row)//2]) if value)
    r, c = left
    collision[r][len(collision[0]) - 1 - c] = 9
    assert any("mirror destination" in reason for reason in gen.self_check(collision))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    gen = _load()
    random.seed(778899)
    state_before = random.getstate()
    first = gen.generate(1234, 2, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(1234, 2, difficulty="hard")
    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(1234, 2, difficulty="hard")
