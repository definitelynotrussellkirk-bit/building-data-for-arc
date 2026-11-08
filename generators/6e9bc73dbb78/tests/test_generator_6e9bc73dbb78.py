from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.6e9bc73dbb78.generator")

ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _grid(rows):
    if rows and isinstance(rows[0], str):
        return [[int(value) for value in row] for row in rows]
    return copy.deepcopy(rows)


def _all_canonical_pairs():
    row = _canonical_row()
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return [(_grid(pair["input"]), _grid(pair["output"])) for pair in pairs]


def test_canonical_inputs_are_accepted_and_python_mirror_matches():
    for input_grid, output_grid in _all_canonical_pairs():
        assert gen.self_check(input_grid) == []
        before = copy.deepcopy(input_grid)
        assert gen.rule_mirror(input_grid) == output_grid
        assert input_grid == before


def test_exact_override_axes_round_trip_at_boundaries():
    cases = [
        dict(
            grid_h=8,
            grid_w=9,
            n_repeat=2,
            size_profile="target_smaller_each",
            color_order="target_lower",
            position_order="target_first",
        ),
        dict(
            grid_h=14,
            grid_w=16,
            n_repeat=4,
            size_profile="target_equal_total",
            color_order="target_higher",
            position_order="target_last",
        ),
        dict(
            grid_h=8,
            grid_w=9,
            n_repeat=4,
            size_profile="target_larger_each_but_smaller_total",
            color_order="target_lower",
            position_order="target_last",
        ),
        dict(
            grid_h=8,
            grid_w=9,
            n_repeat=4,
            size_profile="target_larger_total",
            color_order="target_higher",
            position_order="target_first",
        ),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, 40 + index, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_schedule_covers_every_declared_semantic_axis_value():
    observed = [gen.observe_overrides(gen.generate(1234, index)) for index in range(60)]
    assert {row["n_repeat"] for row in observed} == {2, 3, 4}
    assert {row["size_profile"] for row in observed} == set(gen.SIZE_PROFILES)
    assert {row["color_order"] for row in observed} == set(gen.COLOR_ORDERS)
    assert {row["position_order"] for row in observed} == set(gen.POSITION_ORDERS)
    assert {gen.schedule_profile(1234, index) for index in range(60)} == set(
        gen.SCHEDULE_PROFILES
    )


def test_generated_examples_refute_canonical_highest_color_shortcut():
    canonical_pairs = _all_canonical_pairs()
    assert all(
        gen.CANONICAL_SHORTCUTS["highest_color"](input_grid) == output_grid
        for input_grid, output_grid in canonical_pairs
    )
    counterexample = gen.generate(
        55,
        17,
        color_order="target_lower",
        position_order="target_last",
        size_profile="target_larger_total",
    )
    assert gen.rule_mirror(counterexample) != gen.CANONICAL_SHORTCUTS[
        "highest_color"
    ](counterexample)


def test_self_check_rejects_four_structural_impostors():
    valid = gen.generate(91, 8)
    facts = gen._scene_facts(valid)
    target_color = facts["target_color"]
    repeat_color = facts["repeat_color"]
    repeat_parts = facts["repeat_components"]

    one_color = copy.deepcopy(valid)
    for r, c in facts["target_component"]:
        one_color[r][c] = repeat_color
    assert gen.self_check(one_color)

    two_singletons = copy.deepcopy(valid)
    for component in repeat_parts[1:]:
        for r, c in component:
            two_singletons[r][c] = 0
    assert gen.self_check(two_singletons)

    no_singleton = copy.deepcopy(valid)
    r, c = next(iter(facts["target_component"]))
    placed = False
    for rr in range(len(no_singleton)):
        for cc in range(len(no_singleton[0])):
            if no_singleton[rr][cc] != 0:
                continue
            if abs(rr - r) + abs(cc - c) <= 1:
                continue
            if all(
                not (0 <= rr + dr < len(no_singleton) and 0 <= cc + dc < len(no_singleton[0]))
                or no_singleton[rr + dr][cc + dc] != target_color
                for dr, dc in gen._CARDINAL
            ):
                no_singleton[rr][cc] = target_color
                placed = True
                break
        if placed:
            break
    assert placed
    assert gen.self_check(no_singleton)

    yellow_input = copy.deepcopy(valid)
    rr, cc = next(iter(facts["target_component"]))
    yellow_input[rr][cc] = 4
    assert gen.self_check(yellow_input)


def test_negative_recombination_is_rejected():
    grid = gen.generate(2026, 19, n_repeat=3)
    facts = gen._scene_facts(grid)
    impostor = copy.deepcopy(grid)
    replacement = next(color for color in gen._LEGAL_COLORS if color not in facts["counts"])
    for r, c in facts["repeat_components"][0]:
        impostor[r][c] = replacement
    errors = gen.self_check(impostor)
    assert any("exactly one color with one connected component" in error for error in errors)


def test_deterministic_fresh_returns_and_global_rng_preserved():
    random.seed(8675309)
    expected = [random.random() for _ in range(5)]
    random.seed(8675309)
    first = gen.generate(321, 12, difficulty="medium")
    actual = [random.random() for _ in range(5)]
    second = gen.generate(321, 12, difficulty="medium")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert actual == expected
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_unknown_override_and_invalid_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")
