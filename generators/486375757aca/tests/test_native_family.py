"""Literal seeded-frame state transitions and native episode contracts."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"


def family():
    assert SOURCE.is_file(), "Native seeded-frame family is not implemented"
    spec = importlib.util.spec_from_file_location("frames_native_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_default_and_distinct_alternative():
    mod = family()
    assert hashlib.sha256(mod.program().encode()).hexdigest() == "a19a4990bac925a40190e810e985b52023a5854b4dcde3769b2251fa35432e8e"
    assert mod.program() == mod.program({"post": "none"})
    assert mod.program({"post": "largest_to_8"}) != mod.program()


def test_last_seed_fills_complete_interior_then_recolors_region():
    grid = [[1, 1, 1, 1, 1, 1], [1, 2, 0, 0, 0, 1],
            [1, 0, 0, 3, 0, 1], [1, 0, 0, 0, 0, 1], [1, 1, 1, 1, 1, 1]]
    original = deepcopy(grid)
    mod = family()
    for post, color in (("none", 3), ("largest_to_8", 8)):
        want = [[1] * 6] + [[1] + [color] * 4 + [1] for _ in range(3)] + [[1] * 6]
        assert mod.transform(grid, {"post": post}) == want
    assert grid == original


def test_touching_frames_are_one_object_and_internal_blue_is_overwritten():
    grid = [[1, 1, 1, 0, 0, 0], [1, 2, 1, 1, 1, 1],
            [1, 1, 1, 1, 3, 1], [0, 0, 0, 1, 1, 1]]
    want = [[1, 1, 1, 0, 0, 0], [1, 3, 3, 3, 3, 1],
            [1, 3, 3, 3, 3, 1], [0, 0, 0, 1, 1, 1]]
    assert family().transform(grid) == want


@pytest.mark.parametrize("post,outer", [("none", 4), ("largest_to_8", 8)])
def test_nested_boxes_keep_original_objects_original_seeds_and_order(post, outer):
    grid = [[1] * 7, [1, 2, 0, 0, 0, 0, 1], [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 3, 1, 0, 1], [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 4, 1], [1] * 7]
    want = [[1] * 7] + [[1] + [outer] * 5 + [1] for _ in range(5)] + [[1] * 7]
    want[3][3] = 3
    assert family().transform(grid, {"post": post}) == want


def test_all_largest_ties_include_freestanding_objects():
    grid = [[1, 1, 1, 1, 0, 0, 0, 0], [1, 2, 0, 1, 0, 4, 4, 0],
            [1, 1, 1, 1, 0, 0, 0, 0], [0] * 8]
    want = deepcopy(grid)
    want[1] = [1, 8, 8, 1, 0, 8, 8, 0]
    assert family().transform(grid, {"post": "largest_to_8"}) == want


def test_disconnected_equal_colors_are_not_aggregated():
    grid = [[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 1, 0, 3, 3, 3, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0], [0] * 12]
    want = deepcopy(grid)
    want[1][1:5] = [8] * 4
    assert family().transform(grid, {"post": "largest_to_8"}) == want


def test_open_blue_object_with_seeded_bbox_is_an_explicit_native_extension():
    grid = [[1, 0, 0], [1, 2, 0], [1, 1, 1]]
    assert family().transform(grid, {"post": "largest_to_8"}) == [[1, 0, 0], [1, 8, 0], [1, 1, 1]]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_prefixes_determinism_novelty_and_matched_inputs(seed):
    mod = family()
    shared_inputs = None
    fingerprints = set()
    for setting in mod.SETTINGS:
        bank = mod.generate(seed, setting, demos=6, queries=4)
        assert bank == mod.generate(seed, setting, demos=6, queries=4)
        inputs = [pair["input"] for pair in bank["train"] + bank["test"]]
        if shared_inputs is not None:
            assert inputs == shared_inputs
        shared_inputs = deepcopy(inputs)
        assert len({json.dumps(grid) for grid in inputs}) == 10
        for demos, queries in ((2, 1), (3, 4), (6, 2)):
            smaller = mod.generate(seed, setting, demos=demos, queries=queries)
            assert smaller["train"] == bank["train"][:demos]
            assert smaller["test"] == bank["test"][:queries]
            assert smaller["program_solution"] == mod.program(setting)
            assert smaller["settings"] == setting
        fingerprints.add(json.dumps([pair["output"] for pair in bank["train"][:2]]))
        bank["train"][0]["input"][0][0] = -1
        assert mod.generate(seed, setting, 6, 4)["train"][0]["input"][0][0] != -1
    assert len(fingerprints) == 2
    default = mod.generate(seed)
    assert len(default["train"]) == 3 and len(default["test"]) == 4
    assert default == mod.generate(seed)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_substantive_30_square_and_small_boundary_profiles(seed):
    mod = family()
    bank = mod.generate(seed, {"post": "none"}, 6, 4)
    pairs = bank["train"] + bank["test"]
    assert any(len(pair["input"]) == len(pair["input"][0]) == 3 for pair in pairs)
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    for pair in large:
        grid, output = pair["input"], pair["output"]
        assert sum(value != 0 for row in grid for value in row) >= 300
        assert sum(a != b for source, target in zip(grid, output) for a, b in zip(source, target)) >= 250
        assert all(any(grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
                   for r0 in (0, 15) for c0 in (0, 15))
        assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid) and any(row[-1] for row in grid)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"seed": "1"}, {"seed": -1}, {"seed": 2**63},
    {"demos": True}, {"demos": 1}, {"demos": 7}, {"demos": 3.0},
    {"queries": False}, {"queries": 0}, {"queries": 5}, {"queries": "4"},
    {"settings": {}}, {"settings": {"post": "other"}},
    {"settings": {"post": "none", "extra": 1}}, {"settings": []},
])
def test_strict_request_controls(kwargs):
    request = {"seed": 0, "settings": {"post": "none"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        family().generate(**request)


@pytest.mark.parametrize("grid", [
    [], [[]], [[1] * 3, []], ((1, 1, 1),) * 3, [[True] * 3] * 3,
    [[1.0] * 3] * 3, [["1"] * 3] * 3, [[-1] * 3] * 3, [[10] * 3] * 3,
    [[0] * 3] * 3, [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
    [[1, 0, 0], [0, 2, 0], [0, 0, 0]], [[1] * 31] * 3, [[1] * 3] * 31,
])
def test_strict_grid_and_seeded_bbox_validation(grid):
    with pytest.raises(ValueError):
        family().transform(grid)
