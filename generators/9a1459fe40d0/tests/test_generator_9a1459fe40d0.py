from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.9a1459fe40d0.generator"
)
ROOT = find_root(__file__)


def _generated_pair(seed: int, sample_index: int, difficulty: str):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_owned_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_exact_profile_overrides_are_observable_and_unknown_keys_reject():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(1000 + index, index, scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_profile="canonical_6x11")


def test_generated_scene_exercises_every_decisive_semantic_branch():
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(2000 + index, index, difficulty=band)
            facts, errors = gen._analyze(grid)
            assert errors == []
            assert facts["left_only"]
            assert facts["right_only"]
            assert facts["both_same"]
            assert facts["both_different"]
            assert 7 not in facts["payload_colors"]
            output = gen.rule_mirror(grid)
            assert any(7 in row for row in output)
            assert all(output[row][facts["bar_col"]] == 0 for row in range(len(output)))
            assert all(
                output[row][col] == 0
                for row in range(len(output))
                for col in range(facts["bar_col"] + 1)
            )


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(99, 7, scene_profile="canonical_7x11")
    facts, errors = gen._analyze(grid)
    assert errors == []
    b = facts["bar_col"]

    no_bar = copy.deepcopy(grid)
    no_bar[0][b] = 0
    assert any("full-height" in item for item in gen.self_check(no_bar))

    input_orange = copy.deepcopy(grid)
    input_orange[1][0] = 7
    assert any("reserved" in item for item in gen.self_check(input_orange))

    no_left_only = copy.deepcopy(grid)
    for row, col, _color in facts["left_only"]:
        no_left_only[row][2 * b - col] = no_left_only[row][col]
    assert any("left-only" in item for item in gen.self_check(no_left_only))

    no_right_only = copy.deepcopy(grid)
    for row, col, color in facts["right_only"]:
        no_right_only[row][col] = color
    assert any("right-only" in item for item in gen.self_check(no_right_only))

    no_matched = copy.deepcopy(grid)
    for row, col, _color in facts["both_same"]:
        no_matched[row][2 * b - col] = 0
    for row, col, _left, _right in facts["both_different"]:
        no_matched[row][2 * b - col] = 0
    assert any("doubly occupied" in item for item in gen.self_check(no_matched))


def test_raw_value_inequality_shortcut_fits_canonical_but_not_generation():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert all(gen._raw_value_inequality(pair["input"]) == pair["output"] for pair in pairs)
    for index in range(12):
        grid = gen.generate(3000 + index, index, difficulty="medium")
        assert gen._raw_value_inequality(grid) != gen.rule_mirror(grid)


def test_two_demo_windows_are_identifiable_against_named_competitors():
    sequence = [_generated_pair(4000 + i, i, "hard") for i in range(16)]
    for start in range(len(sequence) - gen.EXAMPLES_NEEDED):
        demos = sequence[start : start + gen.EXAMPLES_NEEDED]
        query = sequence[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []


def test_replay_fresh_returns_and_global_rng_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(5000, 17, difficulty="easy")
    assert random.getstate() == state
    second = gen.generate(5000, 17, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
