from __future__ import annotations

import copy
import importlib
import random
from itertools import product

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "474634a9f7b7"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")



def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_and_every_canonical_pair():
    assert MODULE.RULE_HASH == "36dadf3bcc6b"
    for pair in _canonical_pairs():
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        assert MODULE.self_check(grid) == []
        assert MODULE.strict_canonical_like(grid) == []
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert grid == original


def test_four_slot_schedule_covers_sides_and_canonical_anchors():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(11):
            observed = [
                MODULE.observe_overrides(MODULE.generate(seed, index, difficulty=difficulty))
                for index in range(8)
            ]
            for start in range(4):
                window = observed[start : start + 4]
                assert {item["target_side"] for item in window} == set(MODULE.SIDES)
                assert sum(
                    item["grid_h"] == item["grid_w"] == 16 for item in window
                ) == 2


def test_every_declared_override_is_exact_and_cross_product_safe():
    for grid_h, grid_w, target_side, target_size in product(
        MODULE.GRID_SIZES, MODULE.GRID_SIZES, MODULE.SIDES, MODULE.TARGET_SIZES
    ):
        expected = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "target_side": target_side,
            "target_size": target_size,
        }
        grid = MODULE.generate(731, 19, difficulty="hard", **expected)
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        assert all(observed[key] == value for key, value in expected.items())


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override key"):
        MODULE.generate(0, 0, texture="no_target")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=17)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, target_side="diagonal")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, target_size=21)


def test_rule_changes_exactly_six_cells_and_keeps_target_tip():
    for seed in range(31):
        for index in range(8):
            grid = MODULE.generate(seed, index)
            analysis = MODULE._analyze(grid)
            output = MODULE.rule_mirror(grid)
            changed = {
                (row, col)
                for row in range(len(grid))
                for col in range(len(grid[0]))
                if grid[row][col] != output[row][col]
            }
            assert len(changed) == 6
            target = analysis["target"]
            tr, tc = target["tip"]
            assert output[tr][tc] == target["color"]
            assert set(analysis["bar"]) <= changed
            for component in analysis["components"]:
                if component is target:
                    continue
                assert component["tip"] in changed
                row, col = component["tip"]
                assert output[row][col] == 8


def test_every_sliding_lesson_refutes_declared_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(19):
            for start in range(8):
                demos = []
                for index in range(start, start + MODULE.EXAMPLES_NEEDED):
                    grid = MODULE.generate(seed, index, difficulty=difficulty)
                    demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                query_grid = MODULE.generate(
                    seed, start + MODULE.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
                assert MODULE.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    valid = MODULE.generate(44, 0)

    missing_object = copy.deepcopy(valid)
    component = MODULE._analyze(missing_object)["components"][0]
    for row, col in component["cells"]:
        missing_object[row][col] = 8
    assert MODULE.self_check(missing_object)

    tied_largest = copy.deepcopy(valid)
    analysis = MODULE._analyze(tied_largest)
    second = max(
        (component for component in analysis["components"] if component is not analysis["target"]),
        key=lambda component: component["size"],
    )
    for row, col in second["cells"]:
        tied_largest[row][col] = 8
    replacement = MODULE._component_cells(
        second["side"], analysis["target"]["size"], len(valid), len(valid[0]), random.Random(0)
    )
    for row, col in replacement:
        tied_largest[row][col] = second["color"]
    assert any("largest object must be unique" in error for error in MODULE.self_check(tied_largest))

    split_small = copy.deepcopy(valid)
    smallest = min(MODULE._analyze(split_small)["components"], key=lambda item: item["size"])
    ordered = sorted(smallest["cells"], key=lambda cell: (cell[0], cell[1]))
    middle = next(
        cell
        for cell in ordered
        if sum(neighbor in smallest["cells"] for neighbor in MODULE._neighbors8(cell)) >= 2
    )
    split_small[middle[0]][middle[1]] = 8
    assert MODULE.self_check(split_small)

    occupied_bar = copy.deepcopy(valid)
    bar_cell = MODULE._analyze(occupied_bar)["bar"][1]
    occupied_bar[bar_cell[0]][bar_cell[1]] = 8
    occupied_bar[bar_cell[0]][bar_cell[1]] = next(
        color for color in range(10) if color not in {8, *{v for row in valid for v in row}}
    )
    assert MODULE.self_check(occupied_bar)

    malformed = copy.deepcopy(valid)
    malformed[0] = malformed[0][:-1]
    assert MODULE.self_check(malformed)


def test_determinism_fresh_returns_and_global_rng_state():
    global_state = random.getstate()
    first = MODULE.generate(12345, 9, difficulty="medium")
    second = MODULE.generate(12345, 9, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert random.getstate() == global_state


def test_shape_family_override_emits_distinct_lawful_target_geometries():
    """Every advertised family must be observable and materially different."""
    assert set(MODULE.SHAPE_FAMILIES) == {"layered", "branched"}
    for target_side, target_size in product(MODULE.SIDES, MODULE.TARGET_SIZES):
        grids = {}
        target_cells = {}
        for family in MODULE.SHAPE_FAMILIES:
            grid = MODULE.generate(991, 6, difficulty="hard",
                                   grid_h=20, grid_w=20,
                                   target_side=target_side,
                                   target_size=target_size,
                                   shape_family=family)
            assert MODULE.self_check(grid) == []
            observed = MODULE.observe_overrides(grid)
            assert observed["shape_family"] == family
            assert observed["target_side"] == target_side
            assert observed["target_size"] == target_size
            grids[family] = grid
            target_cells[family] = MODULE._analyze(grid)["target"]["cells"]
        assert grids["layered"] != grids["branched"]
        assert target_cells["layered"] != target_cells["branched"]


def test_default_sampler_reaches_both_shape_families_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        observed = {
            MODULE.observe_overrides(MODULE.generate(seed, index, difficulty=difficulty))[
                "shape_family"
            ]
            for seed in range(8)
            for index in range(8)
        }
        assert observed == set(MODULE.SHAPE_FAMILIES)


def test_shape_family_override_participates_in_full_declared_cross_product():
    for grid_h, grid_w, target_side, target_size, shape_family in product(
        MODULE.GRID_SIZES, MODULE.GRID_SIZES, MODULE.SIDES,
        MODULE.TARGET_SIZES, MODULE.SHAPE_FAMILIES
    ):
        expected = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "target_side": target_side,
            "target_size": target_size,
            "shape_family": shape_family,
        }
        grid = MODULE.generate(881, 3, difficulty="medium", **expected)
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == expected
