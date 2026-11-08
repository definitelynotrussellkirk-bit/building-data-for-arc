"""Focused regression tests for the c7c6836fd350 generator repair."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.c7c6836fd350 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "c7c6836fd350"
BANDS = ("easy", "medium", "hard")


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exactly_supported():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "0af61c7b2115"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_override_axes_roundtrip_for_every_value_and_band():
    case = 0
    for band in BANDS:
        for palette_profile in gen.PALETTE_PROFILES:
            for bbox_profile in gen.BBOX_PROFILES:
                requested = {
                    "palette_profile": palette_profile,
                    "bbox_profile": bbox_profile,
                }
                grid = gen.generate(
                    20_000 + case,
                    case,
                    difficulty=band,
                    **requested,
                )
                assert gen.self_check(grid, meta={"overrides": requested}) == []
                assert gen.observe_overrides(grid) == requested
                case += 1


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"typo_axis": "plain"}, "unknown override"),
        ({"palette_profile": "rainbow"}, "palette_profile"),
        ({"bbox_profile": "diagonal"}, "bbox_profile"),
    ],
)
def test_unknown_and_invalid_overrides_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        gen.generate(1, 0, difficulty="easy", **kwargs)


def test_every_four_slot_window_is_complete_and_lesson_identifiable():
    for band in BANDS:
        pairs = [_pair(31_415, index, band) for index in range(16)]
        for start in range(12):
            demos = pairs[start : start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            observed_profiles = {
                gen.schedule_profile(31_415, index, band)
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            }
            assert observed_profiles == set(gen.SCHEDULE_PROFILES)
            assert gen.lesson_identifiable(demos, query) == []


def test_named_witnesses_refute_their_claimed_rivals():
    grids = [gen.generate(7_700, index, difficulty="hard") for index in range(4)]
    expected = [gen.rule_mirror(grid) for grid in grids]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        hits = [
            (grid, answer)
            for grid, answer in zip(grids, expected)
            if gen.SEMANTIC_WITNESSES[witness_name](grid)
        ]
        assert hits, witness_name
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != answer for grid, answer in hits), (
                witness_name,
                rival_name,
            )


def test_shortcuts_fit_named_anchors_but_are_killed_by_counterexamples():
    canonical = canonical_pairs(TASK_ID)
    for pair in canonical:
        assert gen.SEMANTIC_RIVALS["bbox_of_all_nonzero_cells"](pair["input"]) == pair["output"]
        assert gen.SEMANTIC_RIVALS["bbox_of_modal_nonzero_color"](pair["input"]) == pair["output"]

    corner_anchor = gen.generate(123, 0, difficulty="medium")
    split_extrema = gen.generate(123, 1, difficulty="medium")
    decoy = gen.generate(123, 2, difficulty="medium")
    assert gen.SEMANTIC_RIVALS["bbox_from_row_major_endpoints"](
        corner_anchor
    ) == gen.rule_mirror(corner_anchor)
    assert gen.SEMANTIC_RIVALS["bbox_from_row_major_endpoints"](
        split_extrema
    ) != gen.rule_mirror(split_extrema)
    assert gen.SEMANTIC_RIVALS["bbox_of_all_nonzero_cells"](
        decoy
    ) != gen.rule_mirror(decoy)
    assert gen.SEMANTIC_RIVALS["bbox_of_modal_nonzero_color"](
        decoy
    ) != gen.rule_mirror(decoy)


def test_targeted_structural_impostors_are_rejected():
    too_many_green = gen.generate(60, 2, difficulty="medium")
    zero = next(
        (row, col)
        for row in range(len(too_many_green))
        for col in range(len(too_many_green[0]))
        if too_many_green[row][col] == 0
    )
    too_many_green[zero[0]][zero[1]] = 3

    narrow_bbox = [[0] * 8 for _ in range(6)]
    for row, col in ((1, 1), (1, 3), (2, 2)):
        narrow_bbox[row][col] = 3

    malformed_decoy = gen.generate(61, 0, difficulty="medium")
    zero = next(
        (row, col)
        for row in range(len(malformed_decoy))
        for col in range(len(malformed_decoy[0]))
        if malformed_decoy[row][col] == 0
    )
    malformed_decoy[zero[0]][zero[1]] = 2

    decoy_inside_bbox = [[0] * 10 for _ in range(8)]
    for row, col in ((2, 4), (5, 2), (3, 7)):
        decoy_inside_bbox[row][col] = 3
    for col in range(2, 8):
        decoy_inside_bbox[4][col] = 8

    impostors = {
        "six_green_cells": too_many_green,
        "bbox_too_short": narrow_bbox,
        "one_cell_decoy": malformed_decoy,
        "decoy_inside_green_bbox": decoy_inside_bbox,
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_strict_profile_has_exact_half_support_in_each_band():
    for band in BANDS:
        accepted = 0
        for offset in range(200):
            grid = gen.generate(80_000 + offset, offset, difficulty=band)
            accepted += not bool(gen.strict_canonical_like(grid))
        assert accepted == 100
        assert accepted / 200 >= gen.MIN_STRICT_FRAC


def test_generation_is_replayable_fresh_and_global_rng_pure():
    random.seed(2026_0815)
    before = random.getstate()
    first = gen.generate(71, 9, difficulty="hard")
    intervening = gen.generate(72, 10, difficulty="easy")
    second = gen.generate(71, 9, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    snapshot = copy.deepcopy(second)
    first[0][0] = (first[0][0] + 1) % 10
    assert second == snapshot
    assert first != second
    assert first != intervening
