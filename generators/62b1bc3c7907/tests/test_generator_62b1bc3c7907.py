from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.62b1bc3c7907.generator")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_hash_and_canonical_pairs_are_pinned_and_accepted():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "0d90669b637e"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_generated_scenes_preserve_ferrers_header_grammar_across_bands():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = gen.generate(81000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            observed = gen.observe_overrides(grid)
            assert observed["scene_profile"] == gen.schedule_profile(
                81000 + sample_index, sample_index, band
            )
            h, w = len(grid), len(grid[0])
            row_widths = [grid[r][0] for r in range(1, h)]
            expected_top = [sum(width > c for width in row_widths) for c in range(w - 1)]
            assert grid[0][1:] == expected_top
            assert all(grid[r][c] == 0 for r in range(1, h) for c in range(1, w))


def test_exact_scene_profile_overrides_are_observable_and_unknown_keys_fail():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(91000, 7, difficulty="easy", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(91000, 7, difficulty="easy", typo_profile="5x5_anchor")


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(123456, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123456, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_self_check_rejects_targeted_semantic_impostors():
    base = gen.generate(44000, 0, difficulty="medium")

    blank = [[0 for _ in row] for row in base]
    assert gen.self_check(blank)

    body_noise = copy.deepcopy(base)
    body_noise[1][1] = 9
    assert gen.self_check(body_noise)

    bad_corner = copy.deepcopy(base)
    bad_corner[0][0] = 1
    assert gen.self_check(bad_corner)

    nonmonotone = copy.deepcopy(base)
    nonmonotone[1][0], nonmonotone[2][0] = nonmonotone[2][0], nonmonotone[1][0]
    assert gen.self_check(nonmonotone)

    inconsistent_top = copy.deepcopy(base)
    inconsistent_top[0][1] = max(0, inconsistent_top[0][1] - 1)
    assert gen.self_check(inconsistent_top)


def test_negative_recombination_is_rejected_even_though_selected_rule_ignores_top_header():
    base = gen.generate(55000, 1, difficulty="easy")
    expected = gen.rule_mirror(base)
    recombined = copy.deepcopy(base)
    # Replace a decisive top-header count with a value not present anywhere in
    # the remaining top row. The selected Racket rule reads only column 0, so
    # the oracle answer remains executable/equal while the teaching grammar
    # must reject the inconsistent dual-header scene.
    remaining = set(recombined[0][2:])
    replacement = next(v for v in range(0, len(recombined)) if v not in remaining and v != recombined[0][1])
    recombined[0][1] = replacement
    assert gen.self_check(recombined)
    assert gen.rule_mirror(recombined) == expected


def test_every_three_demo_sliding_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(gen.generate(66000, index, difficulty=band))
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            query = _pair(gen.generate(66000, start + gen.EXAMPLES_NEEDED, difficulty=band))
            assert gen.lesson_identifiable(demos, query) == []


def test_each_generated_scene_refutes_every_named_rival():
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(77000, 3, difficulty=band)
        truth = gen.rule_mirror(grid)
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != truth
