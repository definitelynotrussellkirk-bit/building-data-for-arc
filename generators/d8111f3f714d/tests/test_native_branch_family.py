"""Behavioral contract for the native branch-direction family."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/d8111f3f714d/workspace/parametric"


def load(name="native_family"):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing native module: {path}"
    spec = importlib.util.spec_from_file_location(f"_branch_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(ep, split):
    return [p["input"] for p in ep[split]]


def test_exact_default_and_native_adapter_contract():
    family, adapter = load(), load("adapter")
    canonical = {v["program_solution"] for v in Catalog(ROOT).get(family.TASK_ID)["variants"]}
    assert canonical == {family.program()}
    assert adapter.program({}) == family.program()
    assert family.program({"branch_direction": "away_to_edge"}) != family.program()
    assert adapter.generate(0, {}, 3, 4) == family.generate(0, {}, 3, 4)


@pytest.mark.parametrize("seed", [0, 17, 101, 2**63 - 1])
def test_count_prefixes_matched_inputs_and_local_randomness(seed):
    family = load()
    state = random.getstate()
    full = family.generate(seed, {"branch_direction": "toward_trunk"}, 6, 4)
    short = family.generate(seed, {"branch_direction": "toward_trunk"}, 2, 1)
    other = family.generate(seed, {"branch_direction": "away_to_edge"}, 3, 4)
    assert random.getstate() == state
    assert full["train"][:2] == short["train"]
    assert full["test"][:1] == short["test"]
    assert inputs(full, "train")[:3] == inputs(other, "train")
    assert inputs(full, "test") == inputs(other, "test")
    grids = inputs(full, "train") + inputs(full, "test")
    keys = [tuple(map(tuple, g)) for g in grids]
    assert len(set(keys)) == 10
    assert full["meta"]["construction_attempts"] == [1] * 10
    for a, b in zip(full["test"], other["test"], strict=True):
        assert a["output"] != b["output"]


@pytest.mark.parametrize("seed", [0, 17, 101])
def test_two_core_demos_teach_orientation_sides_and_midpoint_counterexample(seed):
    family = load()
    ep = family.generate(seed, demos=2, queries=4)
    facts = [family.analyze_scene(p["input"]) for p in ep["train"]]
    assert {f["orientation"] for f in facts} == {"v", "h"}
    for f in facts:
        assert f["n_branches"] >= 6
        assert all(f["side_support"].values())
        major = f["height"] if f["orientation"] == "v" else f["width"]
        minor = f["width"] if f["orientation"] == "v" else f["height"]
        assert 0 < f["trunk_start"] < f["trunk_end"] < major - 1
        coords = [p[1] if f["orientation"] == "v" else p[0] for p in f["branches"]]
        assert all(0 < c < minor - 1 for c in coords)
        # A branch between the trunk and the midpoint must extend toward the
        # farther canvas edge under away_to_edge.
        line = f["trunk_line"]
        assert any((c > line and 2 * c < minor - 1) or
                   (c < line and 2 * c > minor - 1) for c in coords)
        assert len({abs(c - line) for c in coords}) >= 3


@pytest.mark.parametrize("setting", ["toward_trunk", "away_to_edge"])
@pytest.mark.parametrize("seed", [0, 17, 101])
def test_substantive_large_query_and_minimum_size(setting, seed):
    family = load()
    ep = family.generate(seed, {"branch_direction": setting}, 3, 4)
    assert (len(ep["test"][0]["input"]), len(ep["test"][0]["input"][0])) == (10, 10)
    big = ep["test"][3]
    f = family.analyze_scene(big["input"])
    assert (f["height"], f["width"]) == (30, 30)
    assert 14 <= f["n_branches"] <= 18
    painted = [(r, c) for r, row in enumerate(big["output"]) for c, v in enumerate(row) if v == 3]
    assert len(painted) >= 70
    assert {(r >= 15, c >= 15) for r, c in painted} == {(False, False), (False, True), (True, False), (True, True)}
    assert any(r in (0, 29) or c in (0, 29) for r, c in f["reds"])
    assert all(big["output"][r][c] == 2 for r, c in f["reds"])


def test_hand_derived_edge_ray_and_rotation_equivariance():
    family = load()
    grid = [[0] * 12 for _ in range(12)]
    for r, c in [(1, 5), (10, 5), (3, 0), (7, 8)]:
        grid[r][c] = 2
    toward = family.python_apply(grid)
    away = family.python_apply(grid, {"branch_direction": "away_to_edge"})
    assert toward[3][:6] == [2, 3, 3, 3, 3, 3]
    assert away[3][:6] == [2, 0, 0, 0, 0, 3]
    assert away[7][8:] == [2, 3, 3, 3]
    rotate = lambda g: [list(row) for row in zip(*g[::-1])]
    for settings in [{}, {"branch_direction": "away_to_edge"}]:
        assert family.python_apply(rotate(grid), settings) == rotate(family.python_apply(grid, settings))


@pytest.mark.parametrize("seed", [True, -1, 1.5, "0", 2**63])
def test_invalid_seeds(seed):
    with pytest.raises(ValueError):
        load().generate(seed)


@pytest.mark.parametrize("demos,queries", [(True, 4), (1, 4), (7, 4), (2.0, 4), (3, True), (3, 0), (3, 5), (3, 1.0)])
def test_invalid_counts(demos, queries):
    with pytest.raises(ValueError):
        load().generate(0, demos=demos, queries=queries)


@pytest.mark.parametrize("settings", [False, "toward_trunk", {"unexpected": 1}, {"branch_direction": 0}, {"branch_direction": "nearest_edge"}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):
        load().generate(0, settings)


def test_grid_validation_rejects_ambiguous_trunks_and_noninteger_cells():
    family = load()
    grid = family.generate(0)["test"][0]["input"]
    bad = deepcopy(grid)
    bad[0][0] = False
    with pytest.raises(ValueError):
        family.analyze_scene(bad)
    bad = [[0] * 10 for _ in range(10)]
    for r, c in [(1, 2), (8, 2), (3, 7), (6, 7)]:
        bad[r][c] = 2
    with pytest.raises(ValueError, match="aligned"):
        family.analyze_scene(bad)


def test_small_inputs_vary_across_seeds():
    family = load()
    keys = {tuple(map(tuple, family.generate(s)["test"][0]["input"])) for s in range(17)}
    assert len(keys) >= 15
