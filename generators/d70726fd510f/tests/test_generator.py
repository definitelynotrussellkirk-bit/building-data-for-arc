"""Task-local regressions: observable controls and finite lesson evidence."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve()
TASK = HERE.parents[1]
for root in HERE.parents:
    if (root / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(root / "shared/runtime"))
        DATA = root / "shared/data/canonical/puzzles.jsonl"
        break
    if (root / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(root))
        DATA = root / "data/canonical/puzzles.jsonl"
        break
spec = importlib.util.spec_from_file_location("task_d70726fd510f", TASK / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def xor_output(grid):
    middle = len(grid[0]) // 2
    return [[2 * ((row[c] != 0) != (row[middle + 1 + c] != 0))
             for c in range(middle)] for row in grid]


def states(grid):
    middle = len(grid[0]) // 2
    return {2 * (row[c] != 0) + (row[middle + 1 + c] != 0)
            for row in grid for c in range(middle)}


def canonical():
    for line in DATA.open():
        row = json.loads(line)
        if row.get("task_id") == "d70726fd510f":
            return row["train"] + row["test"]
    raise AssertionError("canonical task missing")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("target", range(21))
def test_xor_target_is_exact_in_every_band(band, target):
    grid = gen.generate(0, 0, difficulty=band, grid_h=5, panel_w=4,
                        xor_target=target)
    assert sum(value == 2 for row in xor_output(grid) for value in row) == target
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(1, 1), (1, 14), (18, 1), (18, 14)])
def test_dimension_bounds_do_not_depend_on_difficulty(band, height, width):
    grid = gen.generate(7, 3, difficulty=band, grid_h=height, panel_w=width)
    assert (len(grid), len(grid[0])) == (height, 2 * width + 1)
    assert gen.self_check(grid) == []


def test_large_target_expands_unpinned_dimensions():
    grid = gen.generate(3, 0, difficulty="easy", xor_target=252)
    assert (len(grid), len(grid[0])) == (18, 29)
    assert sum(v == 2 for r in xor_output(grid) for v in r) == 252


def test_infeasible_count_names_participating_axes():
    with pytest.raises(ValueError) as exc:
        gen.generate(3, 0, grid_h=1, panel_w=1, xor_target=2)
    assert {"grid_h", "panel_w", "xor_target"} <= set(exc.value.incompatible_axes)


@pytest.mark.parametrize("left", [1, 2, 3, 5, 6, 7, 8, 9])
@pytest.mark.parametrize("right", [1, 2, 3, 5, 6, 7, 8, 9])
def test_all_foreground_pairs_are_visible_exact_controls(left, right):
    options = dict(grid_h=5, panel_w=4, left_color=left, right_color=right,
                   xor_target=8)
    grid = gen.generate(9, 0, **options)
    observed = gen.observe_overrides(grid)
    assert all(observed[key] == value for key, value in options.items())
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("options", [
    {"typo_axis": 3}, {"grid_h": True}, {"panel_w": 2.5},
    {"grid_h": 0}, {"panel_w": 15}, {"left_color": 4},
    {"right_color": 0}, {"left_color": "3"}, {"xor_target": -1},
    {"xor_target": 253}, {"left_density": float("nan")},
    {"right_density": float("inf")}, {"left_density": -0.1},
    {"panel_pattern": "made_up"}, {"texture": "random", "panel_pattern": "blob"},
])
def test_invalid_overrides_fail_loudly(options):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", ["", 0, False, [], {}, "impossible"])
def test_invalid_difficulty_is_not_silently_treated_as_medium(band):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=band)


@pytest.mark.parametrize("grid", [
    [], [[]], [[0], [0, 1]], [[0, 4, 1], [False, 4, 0]],
    [[-1, 0, 4, 0, 0], [0, 1, 4, 0, 1]],
    [[0, 4, 10]], [[0, 4, 1.5]], [[4, 4, 0]],
    [[1, 0, 0]], [[1, 4, 2, 0]], [[1, 2, 4, 0, 0]],
])
def test_validator_rejects_malformed_domain(grid):
    assert gen.self_check(grid)


def test_all_canonical_pairs_match_and_are_accepted():
    pairs = canonical()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert xor_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("pattern", ["random", "blob", "stripes", "checker", "border", "diagonal", "scatter"])
def test_ordinary_patterns_show_entire_occupancy_truth_table(pattern):
    for band in ("easy", "medium", "hard"):
        for index in range(9):
            grid = gen.generate(0, index, difficulty=band, panel_pattern=pattern)
            assert gen.self_check(grid) == []
            assert states(grid) == {0, 1, 2, 3}


@pytest.mark.parametrize("texture,target", [("same_panels", 0), ("all_zero", 0), ("disjoint_panels", 20)])
def test_constant_output_edges_are_lawful_and_explicit(texture, target):
    grid = gen.generate(0, 0, grid_h=5, panel_w=4, texture=texture)
    assert gen.self_check(grid) == []
    assert sum(v == 2 for row in xor_output(grid) for v in row) == target


def test_invisible_palette_requests_are_rejected_instead_of_fabricated():
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, texture="all_zero", left_color=3)
    assert {"texture", "left_color"} <= set(exc.value.incompatible_axes)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=1, panel_w=1, xor_target=1,
                     left_color=3, right_color=7)


@pytest.mark.parametrize("axis", ["left_density", "right_density"])
def test_all_zero_rejects_density_controls_that_cannot_affect_it(axis):
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, texture="all_zero", **{axis: 0.5})
    assert {"texture", axis} <= set(exc.value.incompatible_axes)


def test_broad_profile_keeps_canonical_geometry_and_free_geometry():
    shapes = [(len(grid), len(grid[0])) for seed in range(60)
              for grid in [gen.generate(seed, 2, difficulty="medium")]]
    anchors = shapes.count((5, 9))
    assert 12 <= anchors <= 48
    assert len(set(shapes) - {(5, 9)}) >= 8


def test_declared_shortcuts_really_fit_all_canonical_pairs():
    assert {"fixed_palette_xor", "fixed_shape_xor", "fixed_separator_xor"} <= set(gen.CANONICAL_SHORTCUTS)
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_start_refutes_every_declared_competitor(band):
    for seed in range(4):
        for start in range(3):
            grids = [gen.generate(seed, start + k, difficulty=band) for k in range(4)]
            demos = [{"input": grid, "output": xor_output(grid)} for grid in grids[:3]]
            assert gen.lesson_identifiable(demos, {"input": grids[3]}) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_lesson_check_does_not_read_query_answer():
    grids = [gen.generate(13, k) for k in range(4)]
    demos = [{"input": grid, "output": xor_output(grid)} for grid in grids[:3]]
    without_label = gen.lesson_identifiable(demos, {"input": grids[3]})
    with_poisoned_label = gen.lesson_identifiable(demos, {"input": grids[3], "output": "DO NOT READ"})
    assert without_label == with_poisoned_label == []


def test_lesson_check_rejects_conflicting_or_malformed_visible_labels():
    grid = [[0, 3, 4, 0, 0], [0, 3, 4, 7, 7]]
    pair = {"input": grid, "output": [[0, 2], [2, 0]]}
    bad = copy.deepcopy(pair)
    bad["output"][0][0] = 2
    assert gen.lesson_identifiable([pair, bad], {"input": grid})
    assert gen.lesson_identifiable([{"input": grid, "output": [[0]]}], {"input": grid})
    assert gen.lesson_identifiable([], {"input": grid})


def test_replay_call_order_and_band_masks_are_independent():
    first = gen.generate(21, 0, difficulty="easy")
    gen.generate(100, 200, difficulty="hard")
    assert gen.generate(21, 0, difficulty="easy") == first
    all_bands = [gen.generate(21, 0, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({json.dumps(grid) for grid in all_bands}) == 3
