from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "60b3a4fe8090"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load():
    spec = importlib.util.spec_from_file_location("generator_60_under_test", HOME / "generator.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()
ROOMS = ((0, 0), (0, 6), (6, 0), (6, 6))


def _room_payload(grid, r0, c0):
    command = (r0 + 1, c0 + 1)
    cells = [
        (r, c, grid[r][c])
        for r in range(r0 + 1, r0 + 6)
        for c in range(c0 + 1, c0 + 6)
        if (r, c) != command and grid[r][c] not in (0, 9)
    ]
    colors = {value for _, _, value in cells}
    assert len(colors) == 1
    return next(iter(colors)), {(r, c) for r, c, _ in cells}


def test_rule_hash_is_pinned_and_all_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "ddfddf7b7076"
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_instances_expose_ignored_and_moving_objects(band):
    for index in range(12):
        grid = gen.generate(1701, index, difficulty=band)
        assert gen.self_check(grid) == []
        commands = [grid[r0 + 1][c0 + 1] for r0, c0 in ROOMS]
        payloads = [_room_payload(grid, r0, c0) for r0, c0 in ROOMS]
        colors = [color for color, _ in payloads]
        assert sorted(commands) == [1, 2, 3, 4]
        assert len(set(colors)) == 4
        assert any(color in (1, 2, 3, 4) for color in colors)
        assert any(color in (5, 6, 7, 8) for color in colors)
        assert gen.SEMANTIC_RIVALS["slide_all_colored_objects"](grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("ignored_count", [1, 2, 3])
@pytest.mark.parametrize("object_size", [2, 5])
def test_exact_controls_are_visible_in_pixels(ignored_count, object_size):
    grid = gen.generate(83, 7, ignored_object_count=ignored_count, object_size=object_size)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["ignored_object_count"] == ignored_count
    assert observed["object_size"] == object_size


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"ignored_object_count": 0},
        {"ignored_object_count": 4},
        {"ignored_object_count": True},
        {"object_size": 1},
        {"object_size": 6},
        {"object_size": "3"},
    ],
)
def test_invalid_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)
