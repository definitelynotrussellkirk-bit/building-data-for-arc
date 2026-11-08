"""Focused regressions for generator 73f849e69e0a."""
from __future__ import annotations

import copy
import importlib
import itertools
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "73f849e69e0a"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.73f849e69e0a.generator"
)
BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_accepted() -> None:
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "5a8d0a3601e2"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_round_trip_in_every_band() -> None:
    cases = list(itertools.product((6, 8), (5, 8), (6, 8), (3, 12)))
    assert len(cases) == 16
    for band_index, band in enumerate(BANDS):
        for index, (sep_row, bot_h, bot_w, n_twos) in enumerate(cases):
            requested = {
                "sep_row": sep_row,
                "bot_h": bot_h,
                "bot_w": bot_w,
                "n_twos": n_twos,
            }
            grid = GEN.generate(
                10_000 + 1000 * band_index + index,
                20_000 + index,
                difficulty=band,
                **requested,
            )
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(grid) == []


def test_unknown_override_invalid_override_and_difficulty_fail_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="sep_row"):
        GEN.generate(1, 0, sep_row=5)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_schedule_roles_and_every_three_demo_window_refute_all_named_rivals() -> None:
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for band_index, band in enumerate(BANDS):
        assert {
            GEN.schedule_profile(30_000 + band_index, i, band)
            for i in range(4)
        } == expected_profiles
        for start in range(12):
            seed = 30_000 + 1000 * band_index + start
            grids = [
                GEN.generate(seed, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [_pair(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = _pair(grids[GEN.EXAMPLES_NEEDED])
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), f"rival {name!r} survived a three-demo window at {band}/{start}"


def test_canonical_anchor_and_separator_contrasts_are_real_in_every_band() -> None:
    for band_index, band in enumerate(BANDS):
        for cycle in range(8):
            seed = 40_000 + 1000 * band_index + cycle
            anchor_red = GEN.generate(seed, 4 * cycle, difficulty=band)
            sep7 = GEN.generate(seed, 4 * cycle + 1, difficulty=band)
            sep8 = GEN.generate(seed, 4 * cycle + 2, difficulty=band)
            anchor_no_red = GEN.generate(seed, 4 * cycle + 3, difficulty=band)
            assert GEN.strict_canonical_like(anchor_red) == []
            assert GEN.strict_canonical_like(anchor_no_red) == []
            assert GEN.semantic_observables(anchor_red)["icon_contains_red"] is True
            assert GEN.semantic_observables(anchor_no_red)["icon_contains_red"] is False
            assert GEN.semantic_observables(sep7)["sep_row"] == 7
            assert GEN.semantic_observables(sep8)["sep_row"] == 8
            assert GEN.SEMANTIC_WITNESSES["separator_row_must_be_located"](sep7)
            assert GEN.SEMANTIC_WITNESSES["separator_row_must_be_located"](sep8)


def test_all_declared_structural_mutations_are_rejected() -> None:
    fixtures = list(GEN.mutation_fixtures())
    assert {name for name, _ in fixtures} == {
        "missing_separator",
        "duplicate_separator",
        "nonuniform_2x2_icon_block",
        "foreign_bottom_color",
        "nonzero_top_padding",
        "no_markers",
    }
    for name, grid in fixtures:
        assert GEN.self_check(grid), f"declared impostor {name!r} unexpectedly passed"


def test_determinism_fresh_returns_and_global_rng_isolation() -> None:
    random.seed(20260815)
    state = random.getstate()
    first = GEN.generate(424242, 17, difficulty="hard")
    second = GEN.generate(424242, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert GEN.generate(424242, 17, difficulty="hard") == second


def test_negative_recombination_is_rejected_but_real_racket_oracle_executes() -> None:
    from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule

    valid = GEN.generate(55_555, 1, difficulty="medium")
    invalid = GEN.negative_recombination_fixture(valid)
    assert GEN.self_check(invalid)
    valid_colors = {value for row in valid for value in row}
    invalid_colors = {value for row in invalid for value in row}
    assert len(invalid_colors - valid_colors) == 1

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, invalid)
    finally:
        bridge.shutdown()
    facts = GEN.semantic_observables(valid)
    assert len(output) == 3 * facts["bot_h"]
    assert all(len(row) == 3 * facts["bot_w"] for row in output)
