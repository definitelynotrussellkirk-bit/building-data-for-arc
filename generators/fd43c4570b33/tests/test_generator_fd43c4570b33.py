from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module("puzzle_generators.per_puzzle.fd43c4570b33.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert GEN.RULE_HASH == "050fdd26887a"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        grid = [[int(value) for value in row] for row in pair["input"]]
        expected = [[int(value) for value in row] for row in pair["output"]]
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == expected
        assert grid == original


def test_canonical_profile_schedule_is_exact_and_semantically_complete():
    observed = []
    for sample_index in range(6):
        grid = GEN.generate(811, sample_index, difficulty="medium")
        assert GEN.self_check(grid) == []
        facts = GEN.observe_overrides(grid)
        observed.append((facts["stop_mode"], facts["row_relation"]))
        if sample_index < 3:
            assert GEN.strict_canonical_like(grid) == []
    assert {mode for mode, _ in observed} == set(GEN.STOP_MODES)
    assert {relation for _, relation in observed} == set(GEN.ROW_RELATIONS)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_defaults_are_deterministic_fresh_and_structurally_valid(difficulty):
    for seed in range(30):
        sample_index = 100 + seed
        first = GEN.generate(seed, sample_index, difficulty=difficulty)
        second = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert GEN.self_check(first, difficulty=difficulty) == []
        assert GEN.rule_mirror(first) != first


def test_every_declared_axis_boundary_is_observable():
    cases = [
        {"grid_h": 7}, {"grid_h": 16},
        {"grid_w": 12}, {"grid_w": 24},
        {"left_size": 2}, {"left_size": 6},
        {"right_size": 2}, {"right_size": 6},
        {"gap": 3}, {"gap": 12},
        {"row_relation": "overlap"}, {"row_relation": "disjoint"},
        {"stop_mode": "collision"}, {"stop_mode": "left_wall"},
        {"stop_mode": "right_wall"},
    ]
    for index, overrides in enumerate(cases):
        for difficulty in ("easy", "medium", "hard"):
            grid = GEN.generate(10_000 + index, 41, difficulty=difficulty, **overrides)
            observed = GEN.observe_overrides(grid)
            for key, value in overrides.items():
                assert observed[key] == value
            assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_and_declared_incompatible_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, typo_axis=3)
    with pytest.raises(ValueError) as excinfo:
        GEN.generate(1, 1, row_relation="disjoint", gap=3)
    assert set(excinfo.value.incompatible_axes) == {"row_relation", "gap"}
    with pytest.raises(ValueError) as excinfo:
        GEN.generate(1, 1, gap=12, grid_w=12)
    assert "grid_w" in set(excinfo.value.incompatible_axes)


def test_self_check_rejects_structural_impostors():
    wall_grid = GEN.generate(73, 4, difficulty="medium", stop_mode="left_wall")
    wall_col = GEN.observe_overrides(wall_grid)
    assert wall_col["stop_mode"] == "left_wall"

    truncated_wall = copy.deepcopy(wall_grid)
    col = next(c for c, value in enumerate(truncated_wall[0]) if value == 8)
    truncated_wall[0][col] = 0
    assert any("full grid height" in message for message in GEN.self_check(truncated_wall))

    third_object = copy.deepcopy(wall_grid)
    for row in range(len(third_object)):
        for col in range(len(third_object[0])):
            if third_object[row][col] == 0:
                third_object[row][col] = 6
                break
        else:
            continue
        break
    assert any("exactly two" in message for message in GEN.self_check(third_object))

    disjoint = GEN.generate(74, 5, difficulty="medium", row_relation="disjoint")
    no_wall = [[0 if value == 8 else value for value in row] for row in disjoint]
    assert any("wall-free lessons require occupied-row overlap" in message for message in GEN.self_check(no_wall))

    collision = GEN.generate(75, 3, difficulty="medium", stop_mode="collision", gap=3)
    info = GEN._analysis(collision)
    adjacent = copy.deepcopy(collision)
    shift = info["gap"] - 1
    for row, col in info["right"]:
        adjacent[row][col] = 0
    for row, col in info["right"]:
        adjacent[row][col - shift] = info["right_color"]
    assert GEN.self_check(adjacent)


def test_semantic_rivals_are_actually_counterexampled():
    recolor_witnessed = False
    independent_witnessed = False
    for index in range(60):
        grid = GEN.generate(900 + index, index, difficulty="hard")
        target = GEN.rule_mirror(grid)
        if GEN._recolor_in_place(grid) != target:
            recolor_witnessed = True
        if GEN.observe_overrides(grid)["stop_mode"] != "collision":
            if GEN._independent_to_blocker(grid) != target:
                independent_witnessed = True
        if recolor_witnessed and independent_witnessed:
            break
    assert recolor_witnessed
    assert independent_witnessed
