"""Focused regression tests for generator 7e6a7bb1fcfc."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import defaultdict
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base

REPO_ROOT = Path(__file__).resolve().parents[1]
gen = importlib.import_module("puzzle_generators.per_puzzle.7e6a7bb1fcfc.generator")


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _erase_cells(grid, cells):
    mutated = copy.deepcopy(grid)
    for r, c in cells:
        mutated[r][c] = 0
    return mutated


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    for pair in list(row["train"]) + list(row["test"]):
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_exact_axis_boundaries_and_observation():
    compatible_cases = [
        {"grid_h": 11, "grid_w": 11, "n_frames": 2, "n_shapes": 4},
        {"grid_h": 24, "grid_w": 24, "n_frames": 4, "n_shapes": 8},
        {"n_frames": 4},
        {"n_shapes": 8},
        {"grid_h": 11},
        {"grid_w": 24},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(compatible_cases):
            grid = gen.generate(1000 + index, 2000 + index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            for axis, expected in overrides.items():
                assert observed[axis] == expected

    with pytest.raises(ValueError, match="incompatible overrides"):
        gen.generate(1, 1, grid_h=11, n_frames=4)


def test_default_keyed_axes_equal_returned_scene():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(30):
                grid = gen.generate(30000 + band_index * 1000 + seed, seed * 19 + 7, difficulty=band)
                ctx = captured[-1]
                observed = gen.observe_overrides(grid)
                assert observed == {axis: ctx.axis_value(axis) for axis in gen.AXES}
    finally:
        generator_base.set_ctx_observer(None)


def test_ordinary_lessons_rebut_color_count_and_position_shortcuts():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(40):
            grid = gen.generate(40000 + band_index * 1000 + seed, seed * 23 + 11, difficulty=band)
            scene = gen._analyze_scene(grid)
            frames = scene["frames"]
            shapes = scene["shapes"]
            assert gen.self_check(grid) == []
            assert len(frames) >= 2
            assert len({shape["depth"] for shape in shapes}) >= 3

            by_input_color = defaultdict(set)
            by_depth = defaultdict(set)
            for shape in shapes:
                by_input_color[shape["color"]].add(shape["depth"])
                by_depth[shape["depth"]].add(shape["color"])
            assert any(len(depths) >= 2 for depths in by_input_color.values())
            assert any(len(colors) >= 2 for colors in by_depth.values())

            out = gen.rule_mirror(grid)
            frame_cells = {cell for frame in frames for cell in frame["cells"]}
            assert all(out[r][c] == 0 for r, c in frame_cells)
            for shape in shapes:
                expected = gen._DEPTH_COLOR.get(shape["depth"], 1)
                assert {out[r][c] for r, c in shape["cells"]} == {expected}


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(706711)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_structural_impostors_are_rejected():
    base = gen.generate(
        5151,
        6161,
        difficulty="easy",
        grid_h=12,
        grid_w=12,
        n_frames=2,
        n_shapes=4,
    )
    scene = gen._analyze_scene(base)
    outer, inner = scene["frames"]
    shapes = scene["shapes"]

    broken_inner = copy.deepcopy(base)
    r, c = inner["cells"][0]
    broken_inner[r][c] = 0

    one_shape = copy.deepcopy(base)
    for shape in shapes[1:]:
        for r, c in shape["cells"]:
            one_shape[r][c] = 0

    depth_one = [shape for shape in shapes if shape["depth"] == 1]
    assert len(depth_one) >= 2
    one_depth_only = copy.deepcopy(base)
    keep = {cell for shape in depth_one[:2] for cell in shape["cells"]}
    for shape in shapes:
        for r, c in shape["cells"]:
            if (r, c) not in keep:
                one_depth_only[r][c] = 0

    solid_outer = copy.deepcopy(base)
    r1, c1, r2, c2 = outer["box"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            solid_outer[r][c] = outer["color"]

    side_by_side = [[0] * 13 for _ in range(9)]
    gen._draw_frame(side_by_side, (1, 1, 7, 5), 2)
    gen._draw_frame(side_by_side, (1, 7, 7, 11), 4)
    side_by_side[3][3] = 6
    side_by_side[5][9] = 7

    for impostor in (broken_inner, one_shape, one_depth_only, solid_outer, side_by_side):
        assert gen.self_check(impostor)


def test_absent_feature_recombination_is_rejected_by_lesson_grammar():
    base = gen.generate(
        7171,
        8181,
        difficulty="easy",
        grid_h=12,
        grid_w=12,
        n_frames=2,
        n_shapes=4,
    )
    scene = gen._analyze_scene(base)
    inner = scene["frames"][1]
    used = {value for row in base for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    recombined = copy.deepcopy(base)
    for r, c in inner["cells"]:
        recombined[r][c] = replacement
    rr, cc = inner["cells"][0]
    recombined[rr][cc] = 0
    assert replacement not in {value for row in base for value in row}
    assert gen.self_check(recombined)


def test_invalid_calls_reject_loudly():
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 1, grid_h=10)
    with pytest.raises(ValueError):
        gen.generate(1, 1, n_frames=5)
