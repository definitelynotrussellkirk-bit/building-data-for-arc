"""Focused contract tests for the f5a58a06c0b4 boundary-run generator."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.f5a58a06c0b4 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == "c76d55dfa72e"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(6, 6), (10, 16), (24, 24)])
@pytest.mark.parametrize("run_kind", gen.RUN_KINDS)
def test_exact_override_boundaries_are_observable(
    difficulty, grid_h, grid_w, run_kind
):
    grid = gen.generate(
        314159,
        17,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
        run_kind=run_kind,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "run_kind": run_kind,
    }


def test_invalid_or_unknown_overrides_reject_loudly():
    for overrides in (
        {"grid_h": 5},
        {"grid_w": 25},
        {"run_kind": "curve"},
        {"unknown_axis": 1},
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 0, **overrides)


def test_every_sliding_four_example_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            grids = [
                gen.generate(8000 + start, start + offset, difficulty=difficulty)
                for offset in range(5)
            ]
            demos = [_pair(grid) for grid in grids[:4]]
            query = _pair(grids[4])
            assert gen.lesson_identifiable(demos, query) == []
            analyses = [gen._analyze(grid) for grid in grids[:4]]
            assert {item["selected"]["kind"] for item in analyses} == set(
                gen.RUN_KINDS
            )
            assert {item["destination_index"] for item in analyses} == {
                "first",
                "last",
            }


def test_named_witnesses_kill_every_claimed_rival():
    grids = [gen.generate(9191, index, difficulty="medium") for index in range(20)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        fired = [grid for grid in grids if witness(grid)]
        assert fired, witness_name
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != gen.rule_mirror(grid) for grid in fired)


def test_self_check_rejects_four_structural_impostors():
    base = gen.generate(
        20260728,
        3,
        difficulty="medium",
        grid_h=10,
        grid_w=16,
        run_kind="diag_up",
    )

    foreign_palette = copy.deepcopy(base)
    foreign_palette[0][0] = 3

    duplicate_marker = copy.deepcopy(base)
    extra_marker = next(
        (row, col)
        for row, values in enumerate(duplicate_marker)
        for col, value in enumerate(values)
        if value == 7 and not gen._is_boundary(duplicate_marker, row, col)
    )
    duplicate_marker[extra_marker[0]][extra_marker[1]] = 5

    touching_marker = copy.deepcopy(base)
    old_marker = gen._analyze(touching_marker)["marker"]
    touching_marker[old_marker[0]][old_marker[1]] = 7
    boundary = next(
        (row, col)
        for row, values in enumerate(touching_marker)
        for col, _value in enumerate(values)
        if gen._is_boundary(touching_marker, row, col)
    )
    touching_marker[boundary[0]][boundary[1]] = 5

    disconnected_zero = copy.deepcopy(base)
    isolated = next(
        (row, col)
        for row, values in enumerate(disconnected_zero)
        for col, value in enumerate(values)
        if value == 7
        and not gen._is_boundary(disconnected_zero, row, col)
        and all(
            not (
                0 <= row + dr < len(disconnected_zero)
                and 0 <= col + dc < len(disconnected_zero[0])
                and disconnected_zero[row + dr][col + dc] == 0
            )
            for dr, dc in gen._CARDINAL
        )
    )
    disconnected_zero[isolated[0]][isolated[1]] = 0

    for impostor in (
        foreign_palette,
        duplicate_marker,
        touching_marker,
        disconnected_zero,
    ):
        assert gen.self_check(impostor), impostor


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(77, 19, difficulty="hard")
    middle = gen.generate(78, 20, difficulty="easy")
    second = gen.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert middle != first
    assert before == after

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second == gen.generate(77, 19, difficulty="hard")


def test_negative_recombination_with_absent_color_is_rejected():
    grid = gen.generate(4242, 2, difficulty="medium")
    changed = copy.deepcopy(grid)
    row, col = next(
        (row, col)
        for row, values in enumerate(changed)
        for col, value in enumerate(values)
        if value == 7 and not gen._is_boundary(changed, row, col)
    )
    changed[row][col] = 3
    errors = gen.self_check(changed)
    assert errors
    assert any("palette" in error for error in errors)
