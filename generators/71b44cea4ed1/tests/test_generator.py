from __future__ import annotations

import itertools
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "71b44cea4ed1"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
COUNTEREXAMPLES = Path(__file__).resolve().parents[1] / "counterexamples"


def _counterexample(name: str) -> list[list[int]]:
    return json.loads((COUNTEREXAMPLES / name).read_text())


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted() -> None:
    assert gen.RULE_HASH == "814976eb9ffc"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_are_strict_consumed_and_observable() -> None:
    cases = list(itertools.product((7, 16), (7, 16), (2, 3)))
    assert len(cases) == 8
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, (h, w, pair_count) in enumerate(cases):
            grid = gen.generate(
                50_000 + 1000 * band_index + case_index,
                80_000 + case_index,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                pair_count=pair_count,
            )
            assert (len(grid), len(grid[0])) == (h, w)
            assert gen.observe_overrides(grid)["pair_count"] == pair_count
            assert gen.self_check(grid) == []

    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(True, 0, difficulty="easy")
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, -1, difficulty="easy")
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="impossible")
    with pytest.raises((TypeError, ValueError), match="pair_count"):
        gen.generate(1, 0, difficulty="easy", pair_count=True)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", invented_axis=1)


def test_four_sample_schedule_survives_every_query_rotation() -> None:
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert set(gen.DECOY_MODES) == {
        "canonical_profile",
        "axis_aligned+wrong_distance_and_color",
        "wrong_distance_and_color+blocked_midpoint",
        "blocked_midpoint+axis_aligned",
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            pairs = [
                _pair(
                    110_000 + 1000 * band_index + start,
                    start + offset,
                    band,
                )
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_offset, query in enumerate(pairs):
                demos = [
                    pair
                    for pair_offset, pair in enumerate(pairs)
                    if pair_offset != query_offset
                ]
                assert gen.lesson_identifiable(demos, query) == []


def test_canonical_profile_anchor_is_exact_in_every_band() -> None:
    expected_profiles = {(7, 7, 4), (8, 8, 4), (9, 9, 4)}
    observed = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 4, 8, 12, 16):
            grid = gen.generate(20261012, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            observed.add(profile)
            assert profile in expected_profiles
            assert len(gen._fillable_pairs(grid)) == 3
            assert gen.strict_canonical_like(grid) == []
    assert observed == expected_profiles


def test_targeted_structural_impostors_are_rejected() -> None:
    assert gen.self_check([[0] * 7 for _ in range(7)])

    ambiguous = _counterexample("ambiguous_midpoint.json")
    assert any("ambiguous active midpoint" in error for error in gen.self_check(ambiguous))

    unsupported_repeat = _counterexample("unrecognized_repeated_color.json")
    assert gen.self_check(unsupported_repeat)

    invalid_color = gen.generate(43, 2, difficulty="easy")
    invalid_color = deepcopy(invalid_color)
    invalid_color[0][0] = 10
    assert any("invalid color" in error for error in gen.self_check(invalid_color))


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20261012)
    state = random.getstate()
    first = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if second[0][0] != 9 else 8
    assert first != second


def test_declared_witnesses_and_rivals_are_executable_and_pure() -> None:
    grid = gen.generate(909, 1, difficulty="medium")
    original = deepcopy(grid)
    assert set(gen.SEMANTIC_WITNESSES) == {
        "fills_down_right",
        "fills_down_left",
        "near_miss_axis_aligned",
        "near_miss_wrong_distance",
        "near_miss_different_color",
        "near_miss_blocked_midpoint",
    }
    for witness in gen.SEMANTIC_WITNESSES.values():
        assert isinstance(witness(grid), bool)
        assert grid == original
    for rival in gen.SEMANTIC_RIVALS.values():
        first = rival(grid)
        second = rival(grid)
        assert first == second
        assert grid == original
