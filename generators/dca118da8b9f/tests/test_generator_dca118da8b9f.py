"""Focused semantic and contract tests for generator dca118da8b9f."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "dca118da8b9f"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.dca118da8b9f.generator"
)
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/647beeb937e1/"
    "S9_M6__dca118da8b9f.json"
)


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _canonical_pairs():
    row = _canonical_row()
    return [
        (split, index, _grid(pair["input"]), _grid(pair["output"]))
        for split in ("train", "test")
        for index, pair in enumerate(row[split])
    ]


def _empty(height=9, width=11):
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint(grid, bbox, color):
    r1, c1, r2, c2 = bbox
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            grid[row][col] = color


def _valid_fixture():
    grid = _empty()
    _paint(grid, (0, 0, 2, 2), 2)
    _paint(grid, (5, 6, 8, 9), 6)
    return grid


def test_version_rule_hash_and_task_local_target_are_pinned():
    row = _canonical_row()
    canonical = row["program_solution"]
    expected = hashlib.sha256(
        " ".join(canonical.split()).encode()
    ).hexdigest()[:12]
    base = json.loads(BASE_PATH.read_text())
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == expected == "c15061e4149b"
    assert base["racket_target"]["target_code"] == canonical
    assert base["racket_target"]["raw_code"] != canonical


def test_all_canonical_inputs_are_accepted_and_python_rule_is_exact():
    for split, index, input_grid, expected in _canonical_pairs():
        assert MODULE.self_check(input_grid) == [], f"{split}[{index}]"
        assert MODULE.solve_python(input_grid) == expected, f"{split}[{index}]"


def test_all_declared_override_combinations_round_trip_exactly():
    for canvas_profile in MODULE.CANVAS_PROFILES:
        for scene_profile in MODULE.SCENE_PROFILES:
            for palette_band in MODULE.PALETTE_BANDS:
                grid = MODULE.generate(
                    701,
                    19,
                    difficulty="hard",
                    canvas_profile=canvas_profile,
                    scene_profile=scene_profile,
                    palette_band=palette_band,
                )
                assert MODULE.self_check(grid) == []
                assert MODULE.observe_overrides(grid) == {
                    "canvas_profile": canvas_profile,
                    "scene_profile": scene_profile,
                    "palette_band": palette_band,
                }


def test_default_generation_covers_every_linked_profile_and_rule_branch():
    profiles = set()
    shapes = set()
    counts = set()
    for band in ("easy", "medium", "hard"):
        for index in range(160):
            grid = MODULE.generate(9000 + index, index, difficulty=band)
            observed = MODULE.observe_overrides(grid)
            profiles.add(observed["scene_profile"])
            analysis = MODULE._analyze(grid)
            current_shapes = {item["shape"] for item in analysis["components"]}
            shapes.update(current_shapes)
            counts.add(len(analysis["components"]))
            output = MODULE.solve_python(grid)
            assert output != grid
            assert sum(cell == 8 for row in output for cell in row) == 4 * len(
                analysis["components"]
            )
            assert {cell for row in output for cell in row} <= {0, 8}
    assert profiles == set(MODULE.SCENE_PROFILES)
    assert counts == {2, 3}
    assert any(height == 2 and width > 2 for height, width in shapes)
    assert any(width == 2 and height > 2 for height, width in shapes)
    assert any(height == width for height, width in shapes)
    assert any(height != width for height, width in shapes)


def test_determinism_fresh_returns_input_purity_and_global_rng_state():
    random.seed(314159)
    state_before = random.getstate()
    first = MODULE.generate(13, 21, difficulty="medium")
    state_after = random.getstate()
    second = MODULE.generate(13, 21, difficulty="medium")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    preserved = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert second == preserved
    input_before = copy.deepcopy(second)
    MODULE.solve_python(second)
    assert second == input_before


@pytest.mark.parametrize(
    "name,fixture,error_fragment",
    [
        (
            "identity_2x2",
            lambda: (
                lambda grid: (_paint(grid, (0, 0, 1, 1), 2), _paint(grid, (5, 6, 8, 9), 6), grid)[-1]
            )(_empty()),
            "2x2 rectangle",
        ),
        (
            "hollow_rectangle",
            lambda: (
                lambda grid: (_paint(grid, (0, 0, 2, 2), 2), _paint(grid, (5, 6, 8, 9), 6), grid[1].__setitem__(1, 0), grid)[-1]
            )(_empty()),
            "not solid",
        ),
        (
            "touching_rectangles",
            lambda: (
                lambda grid: (_paint(grid, (0, 0, 2, 2), 2), _paint(grid, (3, 3, 5, 5), 6), grid)[-1]
            )(_empty()),
            "one-cell background gap",
        ),
        (
            "duplicate_colors",
            lambda: (
                lambda grid: (_paint(grid, (0, 0, 2, 2), 2), _paint(grid, (5, 6, 8, 9), 2), grid)[-1]
            )(_empty()),
            "rectangle colors must be distinct",
        ),
        (
            "oversize_rectangle",
            lambda: (
                lambda grid: (_paint(grid, (0, 0, 4, 2), 2), _paint(grid, (6, 6, 8, 9), 6), grid)[-1]
            )(_empty()),
            "unsupported shape",
        ),
    ],
)
def test_self_check_rejects_targeted_impostors(name, fixture, error_fragment):
    errors = MODULE.self_check(fixture())
    assert errors, name
    assert error_fragment in errors[0]


def test_negative_recombination_is_rejected_but_racket_oracle_executes():
    grid = _valid_fixture()
    grid[1][1] = 0  # replacement feature is a hole, absent from the other rectangle
    errors = MODULE.self_check(grid)
    assert errors and "not solid" in errors[0]
    rule = _canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=None)
    try:
        output = bridge.eval_text(rule_application(rule, grid))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(grid)
    assert len(output[0]) == len(grid[0])


def test_invalid_override_and_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 1, bogus_axis="x")
    with pytest.raises(ValueError, match="invalid difficulty"):
        MODULE.generate(1, 1, difficulty="impossible")
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, scene_profile="not-a-profile")
