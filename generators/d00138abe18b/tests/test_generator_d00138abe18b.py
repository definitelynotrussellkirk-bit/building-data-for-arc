from __future__ import annotations

import copy
from puzzle_generators.per_puzzle.d00138abe18b import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed, sample_index, difficulty="medium", **overrides):
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_mirror_outputs():
    for pair in canonical_pairs(gen.TASK_ID):
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_input_pure():
    first = gen.generate(1234, 7, difficulty="hard")
    second = gen.generate(1234, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    before = copy.deepcopy(first)
    gen.rule_mirror(first)
    assert first == before


def test_every_exact_profile_is_observable_and_honored():
    for profile in gen.SCENE_PROFILES:
        for seed in range(10):
            grid = gen.generate(seed, seed + 11, scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_override_is_rejected():
    try:
        gen.generate(1, 0, typo_axis="x")
    except TypeError:
        pass
    else:
        raise AssertionError("unknown override key was silently accepted")


def test_three_consecutive_examples_identify_the_rule():
    for start in range(12):
        demos = [_pair(900 + start, start + offset) for offset in range(3)]
        query = _pair(1900 + start, start + 3)
        assert gen.lesson_identifiable(demos, query) == []


def test_mixed_profile_kills_last_and_mode_shortcuts():
    grid = gen.generate(7, 1, scene_profile="mixed_first_witness")
    answer = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS["last_nonzero"](grid) != answer
    assert gen.SEMANTIC_RIVALS["modal_row_color"](grid) != answer


def test_duplicate_profile_kills_deduplication_shortcut():
    grid = gen.generate(7, 2, scene_profile="duplicate_heads_witness")
    answer = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS["deduplicate_heads"](grid) != answer


def test_negative_recombinations_are_rejected():
    valid = gen.generate(17, 0, scene_profile="canonical_uniform")

    singleton_rows = [[0 for _ in row] for row in valid]
    singleton_rows[0][0] = 1
    singleton_rows[2][2] = 2
    singleton_rows[4][4] = 3
    assert gen.self_check(singleton_rows)

    split_run = copy.deepcopy(valid)
    row = next(r for r in split_run if sum(v != 0 for v in r) >= 2)
    occupied = [i for i, value in enumerate(row) if value]
    row[occupied[0] + 1] = 0
    if len(occupied) == 2:
        row[min(len(row) - 1, occupied[-1] + 1)] = row[occupied[-1]]
    assert gen.self_check(split_run)

    three_color_row = copy.deepcopy(valid)
    target = next(r for r in three_color_row if sum(v != 0 for v in r) >= 3)
    occupied = [i for i, value in enumerate(target) if value]
    target[occupied[0]], target[occupied[1]], target[occupied[2]] = 1, 2, 3
    assert gen.self_check(three_color_row)
