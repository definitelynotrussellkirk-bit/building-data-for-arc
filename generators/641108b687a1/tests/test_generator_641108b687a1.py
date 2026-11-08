from __future__ import annotations

import copy
import importlib

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.641108b687a1.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "139629635146"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_four_example_schedule_is_observable_and_identifiable():
    demos = [_pair(411, index) for index in range(gen.EXAMPLES_NEEDED)]
    query = _pair(411, gen.EXAMPLES_NEEDED)
    assert [
        gen.observe_overrides(demo["input"])["scene_profile"] for demo in demos
    ] == list(gen.SCHEDULE_PROFILES)
    assert gen.lesson_identifiable(demos, query) == []


def test_exact_profile_override_and_unknown_override_rejection():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(17, 99, difficulty="hard", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, made_up_axis="typo")


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(23, 0, scene_profile="canonical_anchor")

    overfull = copy.deepcopy(base)
    row = next(index for index, values in enumerate(overfull) if sum(v != 0 for v in values) == 2)
    empty_column = next(index for index, value in enumerate(overfull[row]) if value == 0)
    overfull[row][empty_column] = 9
    assert any("more than two" in error for error in gen.self_check(overfull))

    adjacent = copy.deepcopy(base)
    row = next(index for index, values in enumerate(adjacent) if sum(v != 0 for v in values) == 2)
    color = next(value for value in adjacent[row] if value)
    adjacent[row] = [0] * len(adjacent[row])
    adjacent[row][2] = color
    adjacent[row][3] = color
    assert any("adjacent" in error for error in gen.self_check(adjacent))

    no_positive = [[0] * len(base[0]) for _ in base]
    no_positive[0][1] = 2
    no_positive[0][4] = 3
    assert any("same-color" in error for error in gen.self_check(no_positive))

    ragged = [row[:] for row in base]
    ragged[-1].pop()
    assert any("rectangular" in error for error in gen.self_check(ragged))


def test_named_rivals_are_killed_by_their_witness_profiles():
    expected_profile = {
        "mismatched_pair_stays_unfilled": "mismatched_pair_control",
        "single_marker_stays_unextended": "single_marker_and_reuse",
        "reused_color_is_still_row_local": "single_marker_and_reuse",
        "interior_span_stops_at_markers": "canonical_anchor",
        "boundary_span_is_not_skipped": "boundary_and_both_controls",
    }
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        grid = gen.generate(31, 0, scene_profile=expected_profile[witness_name])
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        official = gen.rule_mirror(grid)
        assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_generation_is_replayable_fresh_and_global_rng_neutral():
    import random

    state = random.getstate()
    first = gen.generate(1234, 17, difficulty="easy")
    second = gen.generate(1234, 17, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert random.getstate() == state
