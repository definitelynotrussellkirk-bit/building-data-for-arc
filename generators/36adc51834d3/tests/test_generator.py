"""Focused regression tests for generator 36adc51834d3.

The test oracle is intentionally local to tests.  The canonical Racket program
remains label authority; these helpers only state the behavior the repaired
input sampler and semantic hooks must expose.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
TASK = "36adc51834d3"
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("reviewed_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return row["train"] + tests
    raise AssertionError("canonical task missing")


def _normalize_grid(grid):
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _crop_after_command(grid):
    clean = _normalize_grid(grid)
    clean[0][0] = 0
    cells = [
        (row, col)
        for row, values in enumerate(clean)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert cells
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [values[left : right + 1] for values in clean[top : bottom + 1]]


def _reference_output(grid):
    crop = _crop_after_command(grid)
    command = _normalize_grid(grid)[0][0]
    return {
        1: deepcopy(crop),
        2: _rot_cw(crop),
        3: _rot_180(crop),
        4: _rot_ccw(crop),
    }[command]


def _pair(grid):
    return {"input": deepcopy(grid), "output": _reference_output(grid)}


def test_canonical_inputs_and_outputs_are_owned_by_the_contract():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _reference_output(pair["input"]) == _normalize_grid(pair["output"])


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 6,
            "grid_w": 6,
            "blob_size": 3,
            "cmd": 1,
            "color_relation": "same",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "blob_size": 10,
            "cmd": 4,
            "color_relation": "different",
        },
    ],
)
def test_every_exact_override_is_constructive_and_observable_in_every_band(band, overrides):
    grid = gen.generate(31415, 9, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5),
        ("grid_w", 15),
        ("blob_size", 2),
        ("blob_size", 11),
        ("cmd", 0),
        ("cmd", 5),
        ("color_relation", "unknown"),
        ("grid_h", True),
        ("cmd", "2"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_four_consecutive_examples_cover_every_command_and_identify_the_lesson():
    grids = [gen.generate(90210, index, difficulty="medium") for index in range(5)]
    demos = [_pair(grid) for grid in grids[:4]]
    query = _pair(grids[4])
    assert [gen.observe_overrides(grid)["cmd"] for grid in grids[:4]] == [1, 2, 3, 4]
    assert gen.lesson_identifiable(demos, query) == []


def test_default_schedule_covers_both_color_relations_and_transform_revealing_shapes():
    commands = set()
    relations = set()
    inputs = set()
    for index in range(128):
        grid = gen.generate(8000 + index, index, difficulty="medium")
        assert grid == gen.generate(8000 + index, index, difficulty="medium")
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        commands.add(observed["cmd"])
        relations.add(observed["color_relation"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
        crop = _crop_after_command(grid)
        views = {
            tuple(map(tuple, crop)),
            tuple(map(tuple, _rot_cw(crop))),
            tuple(map(tuple, _rot_180(crop))),
            tuple(map(tuple, _rot_ccw(crop))),
        }
        assert len(views) == 4
    assert commands == {1, 2, 3, 4}
    assert relations == {"same", "different"}
    assert len(inputs) >= 120


def test_structural_mutations_are_rejected():
    base = gen.generate(
        41,
        3,
        grid_h=8,
        grid_w=9,
        blob_size=6,
        cmd=4,
        color_relation="different",
    )
    fixtures = {}

    missing_command = deepcopy(base)
    missing_command[0][0] = 0
    fixtures["missing_command"] = missing_command

    no_object = [[0 for _ in row] for row in base]
    no_object[0][0] = 2
    fixtures["missing_object"] = no_object

    multicolor = deepcopy(base)
    for row, values in enumerate(multicolor):
        for col, value in enumerate(values):
            if (row, col) != (0, 0) and value:
                multicolor[row][col] = 9 if value != 9 else 8
                break
        else:
            continue
        break
    fixtures["multicolor_object"] = multicolor

    command_corner = deepcopy(base)
    command_corner[0][1] = command_corner[2][2] or 7
    fixtures["command_corner_intrusion"] = command_corner

    for name, grid in fixtures.items():
        assert gen.self_check(grid), f"mutation {name!r} was accepted"


def test_declared_canonical_shortcuts_reproduce_every_canonical_pair():
    """Only hypotheses truly ambiguous on all public pairs may use this name."""
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for index, pair in enumerate(_canonical_pairs()):
            assert shortcut(pair["input"]) == _normalize_grid(pair["output"]), (
                f"{name!r} is a lesson competitor, not a canonical shortcut; "
                f"it already fails public pair {index}"
            )


def test_object_crop_removes_command_when_object_bbox_encloses_corner():
    """The rule clears (0,0) before cropping, even when the bbox contains it."""
    grid = gen.generate(222845685425138, 451, difficulty="easy")
    observed = gen.observe_overrides(grid)
    assert observed["cmd"] == 4
    assert observed["color_relation"] == "different"
    assert gen._crop_object(grid) == _crop_after_command(grid)
    assert all(value != 4 for row in gen._crop_object(grid) for value in row)
