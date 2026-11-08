from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.836938f29751.generator")
TASK_ID = "836938f29751"


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_and_all_canonical_pairs():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "c51a915c15a5"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [6, 12])
@pytest.mark.parametrize("grid_w", [8, 14])
@pytest.mark.parametrize("rect_h", [4, 6])
@pytest.mark.parametrize("rect_w", [4, 7])
@pytest.mark.parametrize("color", [1, 9])
def test_every_boundary_override_cross_is_exact(
    difficulty, grid_h, grid_w, rect_h, rect_w, color
):
    overrides = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "rect_h": rect_h,
        "rect_w": rect_w,
        "color": color,
    }
    grid = GEN.generate(12345, 73, difficulty=difficulty, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_invalid_overrides_and_difficulty_fail_loudly():
    for kwargs in (
        {"difficulty": "expert"},
        {"texture": "noise"},
        {"grid_h": 5},
        {"grid_w": 15},
        {"rect_h": 3},
        {"rect_w": 8},
        {"color": 0},
        {"color": True},
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(909)
    before = random.getstate()
    first = GEN.generate(77, 11, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(77, 11, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


def test_default_keyed_provenance_matches_observed_axes():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(80000 + index, index * 19 + 5, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis in GEN.AXES:
                assert captured[0].axis_value(axis) == observed[axis]


def test_three_example_sliding_windows_are_identifiable_and_refute_rivals():
    for seed in range(12):
        pairs = [_pair(GEN.generate(200000 + seed, index, difficulty="medium")) for index in range(16)]
        for start in range(13):
            demos = pairs[start : start + 3]
            query = pairs[start + 3]
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_self_check_rejects_four_targeted_impostors():
    valid = GEN.generate(404, 1, difficulty="medium", grid_h=10, grid_w=12, rect_h=5, rect_w=6, color=4)
    analysis = GEN._analysis(valid)

    missing_corner = copy.deepcopy(valid)
    missing_corner[analysis["bottom"]][analysis["right"]] = 0
    assert any("exactly 4" in error for error in GEN.self_check(missing_corner))

    mixed_color = copy.deepcopy(valid)
    mixed_color[analysis["top"]][analysis["right"]] = 6
    assert any("share one colour" in error for error in GEN.self_check(mixed_color))

    fifth_marker = copy.deepcopy(valid)
    fifth_marker[analysis["top"] + 1][analysis["left"] + 1] = 4
    assert any("exactly 4" in error for error in GEN.self_check(fifth_marker))

    non_corner_recombination = copy.deepcopy(valid)
    non_corner_recombination[analysis["bottom"]][analysis["right"]] = 0
    non_corner_recombination[analysis["bottom"] - 1][analysis["right"]] = 4
    assert any("two rows" in error or "four rectangle corners" in error for error in GEN.self_check(non_corner_recombination))


def test_negative_recombination_rejected_but_racket_oracle_executes():
    valid = GEN.generate(909, 2, difficulty="hard", grid_h=11, grid_w=13, rect_h=6, rect_w=7, color=8)
    analysis = GEN._analysis(valid)
    recombined = copy.deepcopy(valid)
    recombined[analysis["bottom"]][analysis["right"]] = 0
    recombined[analysis["bottom"] - 1][analysis["right"]] = 8
    assert GEN.self_check(recombined)

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
        assert len(output) == len(recombined)
        assert len(output[0]) == len(recombined[0])
    finally:
        bridge.shutdown()


def test_racket_40_generated_exact_input_pure_and_a_b_a():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        grids = [
            GEN.generate(70000 + index, index * 17 + 3, difficulty=("easy", "medium", "hard")[index % 3])
            for index in range(40)
        ]
        for grid in grids:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before
        a1 = _apply_rule(bridge, fn_name, grids[7])
        b = _apply_rule(bridge, fn_name, grids[31])
        a2 = _apply_rule(bridge, fn_name, grids[7])
        assert a1 == GEN.rule_mirror(grids[7])
        assert b == GEN.rule_mirror(grids[31])
        assert a2 == a1
    finally:
        bridge.shutdown()
