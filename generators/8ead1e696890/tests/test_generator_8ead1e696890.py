from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "8ead1e696890"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"


def _load():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load()


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text(encoding="utf-8").splitlines())
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def _datum(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _counts(gen, grid):
    h, w = len(grid), len(grid[0])
    border = interior = 0
    for _, cells in gen._components(grid):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            border += 1
        else:
            interior += 1
    return border, interior


def test_ordinary_sampler_constructs_three_or_more_border_components(gen):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(12):
            grid = gen.generate(810000 + seed, seed, difficulty=difficulty)
            border, interior = _counts(gen, grid)
            assert border >= 3
            assert interior >= 1
            assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides, expected_shape, expected_counts",
    [
        ({"grid_h": 5}, (5, None), None),
        ({"grid_h": 18}, (18, None), None),
        ({"grid_w": 5}, (None, 5), None),
        ({"grid_w": 18}, (None, 18), None),
        ({"interior_objects": 8}, (None, None), (None, 8)),
        ({"border_objects": 8}, (None, None), (8, None)),
    ],
)
def test_advertised_boundaries_and_object_counts_are_realized(gen, overrides, expected_shape, expected_counts):
    grid = gen.generate(912345, 17, difficulty="medium", **overrides)
    h, w = len(grid), len(grid[0])
    if expected_shape[0] is not None:
        assert h == expected_shape[0]
    if expected_shape[1] is not None:
        assert w == expected_shape[1]
    border, interior = _counts(gen, grid)
    if expected_counts:
        if expected_counts[0] is not None:
            assert border == expected_counts[0]
        if expected_counts[1] is not None:
            assert interior == expected_counts[1]
    assert gen.self_check(grid) == []


def test_palette_and_helpful_texture_controls_change_realized_colors(gen):
    warm = gen.generate(912345, 17, difficulty="medium", palette_kind="warm")
    cool = gen.generate(912345, 17, difficulty="medium", palette_kind="cool")
    assert warm != cool
    warm_texture = gen.generate(912345, 17, difficulty="medium", texture="warm")
    cool_texture = gen.generate(912345, 17, difficulty="medium", texture="cool")
    assert warm_texture != cool_texture
    assert warm_texture == warm
    assert cool_texture == cool


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": True},
        {"grid_w": 4},
        {"interior_objects": 9},
        {"border_objects": 2},
        {"palette_kind": "unknown"},
        {"texture": "unknown"},
        {"palette_size": 3},
        {"n_distinct_colors": 3},
        {"definitely_not_an_axis": 1},
    ],
)
def test_invalid_removed_or_unknown_overrides_fail_closed(gen, overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(912346, 0, **overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"texture": "all_border", "grid_h": 12},
        {"texture": "all_interior", "interior_objects": 4},
        {"texture": "no_components", "palette_kind": "warm"},
    ],
)
def test_degenerate_textures_reject_axes_they_cannot_honor(gen, overrides):
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(912346, 0, **overrides)


def test_incompatible_small_grid_and_many_objects_fails_instead_of_underplacing(gen):
    with pytest.raises(ValueError, match="incompatible|place"):
        gen.generate(11, 0, grid_h=5, grid_w=5, interior_objects=8, border_objects=8)


def test_generated_inputs_are_deterministic_and_canonical_racket_executes(gen):
    first = gen.generate(55, 7, difficulty="medium", border_objects=5, interior_objects=4)
    second = gen.generate(55, 7, difficulty="medium", border_objects=5, interior_objects=4)
    assert first == second
    assert _counts(gen, first) == (5, 4)
    with RacketBridge(timeout=60) as bridge:
        output = normalize_grid(bridge.eval_text(f"({wrap_rule(_canonical_program())} {_datum(first)})"))
    assert len(output) == len(first)
    assert len(output[0]) == len(first[0])
    assert sum(value != 0 for row in output for value in row) > 0
    assert sum(value != 0 for row in output for value in row) < sum(
        value != 0 for row in first for value in row
    )


def test_ordinary_sampler_refutes_keep_only_border_cells_shortcut(gen):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(24):
            grid = gen.generate(930000 + seed, seed, difficulty=difficulty)
            height, width = len(grid), len(grid[0])
            border_components = [
                cells
                for _, cells in gen._components(grid)
                if any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
            ]
            assert any(
                any(0 < r < height - 1 and 0 < c < width - 1 for r, c in cells)
                for cells in border_components
            )
