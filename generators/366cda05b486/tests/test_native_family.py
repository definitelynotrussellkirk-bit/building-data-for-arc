"""Literal graph semantics and native episode boundary contracts."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"


def family():
    assert SOURCE.is_file(), "Native contact-cluster family is not implemented"
    spec = importlib.util.spec_from_file_location("contact_native_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_default_and_meaningful_alternative():
    mod = family()
    assert hashlib.sha256(mod.program().encode()).hexdigest() == "f50313901f961bd1d105eedf9f91e943a0e52d1e0ea092fceb6e500c7eb77db4"
    assert mod.program() == mod.program({"scope": "cluster"})
    assert mod.program({"scope": "farthest"}) != mod.program()


def test_literal_transitive_cluster_and_complete_farthest_object():
    mod = family()
    grid = [[1, 2, 2, 0, 4, 4], [0, 0, 3, 0, 4, 0],
            [5, 5, 3, 0, 4, 0], [5, 0, 0, 0, 0, 0]]
    original = deepcopy(grid)
    assert mod.transform(grid, {"scope": "cluster"}) == [
        [8, 8, 8], [0, 0, 8], [8, 8, 8], [8, 0, 0]]
    assert mod.transform(grid, {"scope": "farthest"}) == [[8, 8], [8, 0]]
    assert grid == original


def test_all_tied_farthest_objects_and_gaps_are_retained():
    grid = [[0, 3, 0], [1, 2, 4], [0, 5, 0]]
    assert family().transform(grid, {"scope": "farthest"}) == [[8, 0], [0, 8], [8, 0]]


def test_shortest_hops_on_a_cycle():
    grid = [[1, 2, 0], [3, 4, 5]]
    assert family().transform(grid, {"scope": "farthest"}) == [[8]]
    # A long same-color arm is one object, not several pixel steps.
    grid = [[1, 2, 2, 2, 2], [3, 0, 0, 0, 2], [4, 0, 0, 0, 2]]
    assert family().transform(grid, {"scope": "farthest"}) == [[8]]


def test_disconnected_equal_colors_do_not_merge_objects():
    grid = [[1, 2, 3, 2], [0, 0, 0, 4]]
    assert family().transform(grid, {"scope": "farthest"}) == [[8]]


def test_diagonal_distractor_is_excluded_and_cyan_is_ordinary():
    grid = [[1, 8, 2, 0], [0, 0, 0, 3], [0, 0, 0, 4]]
    assert family().transform(grid, {"scope": "cluster"}) == [[8, 8, 8]]
    assert family().transform(grid, {"scope": "farthest"}) == [[8]]


@pytest.mark.parametrize("grid", [[[1]], [[0, 0, 0], [0, 1, 0]], [[1, 1], [1, 0]]])
def test_isolated_seed_is_total_for_both_settings(grid):
    mod = family()
    assert mod.transform(grid, mod.SETTINGS[0]) == mod.transform(grid, mod.SETTINGS[1])


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
            assert smaller["settings"] == setting
            assert smaller["program_solution"] == mod.program(setting)
        fingerprints.add(json.dumps([pair["output"] for pair in bank["train"][:2]]))
        bank["train"][0]["input"][0][0] = -1
        assert mod.generate(seed, setting, 6, 4)["train"][0]["input"][0][0] != -1
    assert len(fingerprints) == 2
    default = mod.generate(seed)
    assert len(default["train"]) == 3 and len(default["test"]) == 4
    assert default == mod.generate(seed)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_large_profiles_have_real_content_and_graph_depth(seed):
    mod = family()
    bank = mod.generate(seed, {"scope": "farthest"}, 6, 4)
    large = [pair["input"] for pair in bank["train"] + bank["test"]
             if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 2
    for grid in large:
        assert sum(value != 0 for row in grid for value in row) >= 200
        objects, adjacency, seed_id, distances = mod.analyze(grid)
        assert len(objects) >= 12 and max(distances.values()) >= 8
        assert all(any(grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
                   for r0 in (0, 15) for c0 in (0, 15))


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"seed": "1"}, {"seed": -1}, {"seed": 2**63},
    {"demos": True}, {"demos": 1}, {"demos": 7}, {"demos": 3.0},
    {"queries": False}, {"queries": 0}, {"queries": 5}, {"queries": "4"},
    {"settings": {}}, {"settings": {"scope": "other"}},
    {"settings": {"scope": "cluster", "extra": 1}}, {"settings": []},
])
def test_strict_request_validation(kwargs):
    request = {"seed": 0, "settings": {"scope": "cluster"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        family().generate(**request)


@pytest.mark.parametrize("grid", [
    [], [[]], [[1], []], ((1,),), [[True]], [[1.0]], [["1"]],
    [[1, -1]], [[1, 10]], [[0]], [[1, 0, 1]], [[1, 0], [0, 1]],
    [[1] * 31], [[1] for _ in range(31)],
])
def test_strict_grid_and_unique_seed_validation(grid):
    with pytest.raises(ValueError):
        family().transform(grid)
