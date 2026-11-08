from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "40e128dec2ec"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def _accepted(grid):
    return GEN.self_check(grid) == []


def test_generator_40e128dec2ec_accepts_every_canonical_input():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []


def test_generator_40e128dec2ec_default_schedule_is_structural_and_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(12345, index, difficulty=difficulty) for index in range(4)]
        assert all(_accepted(grid) for grid in grids)
        seen = set()
        for grid in grids[:3]:
            info, errors = GEN._analyse(grid)
            assert errors == []
            seen.update(info["frame_colors"])
        assert seen == {1, 2, 3, 4}
        assert any(GEN._periodic_repeat(grid) for grid in grids[:3])
        assert any(
            4 in GEN._analyse(grid)[0]["frame_colors"]
            and GEN._transpose_differs_from_ccw(grid)
            for grid in grids[:3]
        )


def test_generator_40e128dec2ec_exact_axis_boundaries_are_observable():
    for difficulty in ("easy", "medium", "hard"):
        for h, w in ((9, 13), (9, 24), (18, 13), (18, 24)):
            grid = GEN.generate(9001, 2, difficulty=difficulty, grid_h=h, grid_w=w)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"grid_h": h, "grid_w": w}


def test_generator_40e128dec2ec_is_deterministic_fresh_and_rng_pure():
    random.seed(771)
    state = random.getstate()
    first = GEN.generate(44, 2, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(44, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_generator_40e128dec2ec_self_check_rejects_targeted_impostors():
    base = GEN.generate(314159, 1, difficulty="medium")
    info, errors = GEN._analyse(base)
    assert errors == []

    no_divider = copy.deepcopy(base)
    no_divider[2][0] = 0

    missing_template_colour = copy.deepcopy(base)
    for r in range(2):
        for c in range(len(base[0])):
            if missing_template_colour[r][c] == 3:
                missing_template_colour[r][c] = 2

    broken_frame = copy.deepcopy(base)
    frame = info["frames"][0]
    broken_frame[3 + frame["r1"]][frame["c1"]] = 0

    interior_prefilled = copy.deepcopy(base)
    frame = info["frames"][0]
    interior_prefilled[3 + frame["r1"] + 1][frame["c1"] + 1] = frame["color"]

    extra_lower_object = copy.deepcopy(base)
    placed = False
    for r in range(3, len(base)):
        for c in range(len(base[0])):
            if extra_lower_object[r][c] == 0:
                extra_lower_object[r][c] = 1
                placed = True
                break
        if placed:
            break

    duplicate_frame_colour = copy.deepcopy(base)
    frames = info["frames"]
    old, new = frames[1]["color"], frames[0]["color"]
    for r in range(3 + frames[1]["r1"], 3 + frames[1]["r2"] + 1):
        for c in range(frames[1]["c1"], frames[1]["c2"] + 1):
            if duplicate_frame_colour[r][c] == old:
                duplicate_frame_colour[r][c] = new

    impostors = {
        "no_divider": no_divider,
        "missing_template_colour": missing_template_colour,
        "broken_frame": broken_frame,
        "interior_prefilled": interior_prefilled,
        "extra_lower_object": extra_lower_object,
        "duplicate_frame_colour": duplicate_frame_colour,
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_generator_40e128dec2ec_transpose_authority_refutes_270_degree_rival():
    grid = GEN.generate(8128, 1, difficulty="hard")
    info, errors = GEN._analyse(grid)
    assert errors == []
    assert 4 in info["frame_colors"]
    assert GEN._transpose_differs_from_ccw(grid)
    official = GEN._official_solution(grid)
    rival = GEN._solve_with_mapping(grid, GEN._colour4_ccw)
    assert official != rival


def test_generator_40e128dec2ec_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown overrides"):
        GEN.generate(1, 0, texture="no_frames")
