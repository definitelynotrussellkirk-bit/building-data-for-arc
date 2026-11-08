"""Regression frontier for the two-panel masking task 8921bea21bbb."""
from __future__ import annotations

import copy
import os
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    TASK_ID,
    analyze,
    color2_only_rival,
    independent_rule,
    load_generator,
    split_panels,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "panel_h",
    "panel_w",
    "mask_count",
    "mask_color",
    "right_zero_count",
}


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_exact_axis_contract_are_explicit():
    assert gen.RULE_HASH == "adbc411a920b"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_every_canonical_pair_is_accepted_and_mirrored(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert independent_rule(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(panel_h=5, panel_w=5, mask_count=4, mask_color=1, right_zero_count=0),
        dict(panel_h=8, panel_w=8, mask_count=12, mask_color=8, right_zero_count=4),
        dict(panel_h=6, panel_w=7, mask_count=9, mask_color=2, right_zero_count=3),
    ],
)
def test_every_exact_override_is_observable_in_every_band(band, options):
    grid = gen.generate(20261005, 97, difficulty=band, **options)
    assert gen.self_check(grid) == []
    observed = analyze(grid)
    assert {key: observed[key] for key in options} == options
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == independent_rule(grid)


def test_invalid_calls_are_rejected_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(0, 0, typo_axis=1)
    for value in (True, "6", 6.0):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, panel_h=value)
    for key, value in (
        ("panel_h", 4),
        ("panel_w", 9),
        ("mask_count", 3),
        ("mask_color", 0),
        ("right_zero_count", 5),
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, **{key: value})
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_schedule_supplies_both_canonical_profiles_in_every_band_and_uses_difficulty():
    expected_profiles = {(5, 11, 9), (6, 13, 9)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        for index in range(20):
            grid = gen.generate(77, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            if profile in expected_profiles:
                seen.add(profile)
        assert seen == expected_profiles
    same_call = [gen.generate(91, 3, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in same_call}) == 3


def test_canonical_shortcut_fits_canonical_examples_but_generated_witness_refutes_it():
    pairs = _pairs()
    assert all(color2_only_rival(pair["input"]) == pair["output"] for pair in pairs)
    assert set(gen.CANONICAL_SHORTCUTS) == {"color2_only"}
    assert all(
        gen.CANONICAL_SHORTCUTS["color2_only"](pair["input"]) == pair["output"]
        for pair in pairs
    )
    for band in ("easy", "medium", "hard"):
        witness = gen.generate(404, 1, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["non_two_mask"](witness)
        assert gen.SEMANTIC_RIVALS["color2_only"](witness) != independent_rule(witness)


def test_all_declared_witnesses_refute_their_named_rivals():
    grid = gen.generate(707, 1, panel_h=6, panel_w=6, mask_count=8, mask_color=7, right_zero_count=3)
    expected = independent_rule(grid)
    assert gen.self_check(grid) == []
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        assert gen.SEMANTIC_WITNESSES[witness_name](copy.deepcopy(grid)), witness_name
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](copy.deepcopy(grid)) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_any_three_of_four_scheduled_pairs_eliminate_every_lesson_competitor(band):
    for start in range(8):
        pairs = [
            _pair(gen.generate(8000 + start, start + offset, difficulty=band))
            for offset in range(4)
        ]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_self_check_rejects_prior_divider_crash_and_task_semantic_impostors():
    valid = gen.generate(22, 1, panel_h=5, panel_w=5, mask_count=6, mask_color=4, right_zero_count=2)
    sep, left, right = split_panels(valid)
    malformed = []
    malformed.append([[0] * len(valid[0]) for _ in valid])
    malformed.append([row[:-1] for row in valid])
    no_separator = [row[:sep] + [0] + row[sep + 1 :] for row in valid]
    malformed.append(no_separator)
    second_separator = copy.deepcopy(valid)
    for row in second_separator:
        row[0] = 9
    malformed.append(second_separator)
    mixed_mask = copy.deepcopy(valid)
    first = next((r, c) for r, row in enumerate(left) for c, value in enumerate(row) if value)
    mixed_mask[first[0]][first[1]] = 8 if mixed_mask[first[0]][first[1]] != 8 else 7
    malformed.append(mixed_mask)
    no_overlap = copy.deepcopy(valid)
    for row in range(len(left)):
        for column in range(len(left[0])):
            if left[row][column] != 0:
                no_overlap[row][sep + 1 + column] = 0
    malformed.append(no_overlap)
    for grid in malformed:
        assert gen.self_check(grid), grid


def test_determinism_freshness_and_global_rng_isolation():
    random.seed(991)
    state = random.getstate()
    first = gen.generate(123, 8, difficulty="hard")
    second = gen.generate(123, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
