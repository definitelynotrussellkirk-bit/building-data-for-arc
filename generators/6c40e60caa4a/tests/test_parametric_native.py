"""Behavior tests for the native deepest-vs-all-seeded-frame family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/6c40e60caa4a"
NATIVE = HOME / "workspace/parametric/native.py"


def _load_native():
    if not NATIVE.is_file():
        pytest.fail("native parametric implementation is missing")
    spec = importlib.util.spec_from_file_location("native_6c40_under_test", NATIVE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = rr + dr, cc + dc
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        todo.append(p)
            result.append(cells)
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _contains(box, point):
    r0, c0, r1, c1 = box
    r, c = point
    return r0 < r < r1 and c0 < c < c1


def _strictly_contains(outer, inner):
    return outer[0] < inner[0] and outer[1] < inner[1] and inner[2] < outer[2] and inner[3] < outer[3]


def _oracle(grid, scope):
    frames = [_bbox(cells) for cells in _components(grid, 1)]
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    seeded = [box for box in frames if any(_contains(box, seed) for seed in seeds)]
    if scope == "deepest":
        selected = [box for box in seeded if not any(box != other and _strictly_contains(box, other) for other in seeded)]
    elif scope == "all_seeded":
        selected = seeded
    else:
        raise AssertionError(scope)
    out = copy.deepcopy(grid)
    for r0, c0, r1, c1 in selected:
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 3
    return out


@pytest.fixture(scope="module")
def native():
    return _load_native()


def test_default_program_is_exact_selected_canonical_bytes(native):
    ledger = canonical_path(ROOT)
    programs = {
        row["program_solution"]
        for line in ledger.read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "6c40e60caa4a"
    }
    assert programs == {native.program({"frame_scope": "deepest"})}
    canonical = next(iter(programs))
    assert hashlib.sha256(canonical.encode()).hexdigest() == hashlib.sha256(
        (HOME / "workspace/parametric/canonical.rkt").read_bytes()
    ).hexdigest()
    assert native.program({"frame_scope": "all_seeded"}) != canonical


@pytest.mark.parametrize("settings", [
    None, {}, "deepest", {"frame_scope": True}, {"frame_scope": "other"},
    {"frame_scope": "deepest", "extra": 1},
])
def test_settings_are_exact_and_bounded(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)
    with pytest.raises(ValueError):
        native.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 0.0, "0", None])
def test_seed_is_exact_bounded_integer(native, seed):
    with pytest.raises(ValueError):
        native.sample_inputs(seed)


@pytest.mark.parametrize("demos", [0, 1, 7, True, 3.0, "3", None])
def test_demo_count_is_two_through_six(native, demos):
    with pytest.raises(ValueError):
        native.sample_inputs(0, demos=demos)


@pytest.mark.parametrize("queries", [0, 5, True, 1.0, "1", None])
def test_query_count_is_one_through_four(native, queries):
    with pytest.raises(ValueError):
        native.sample_inputs(0, queries=queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_sampling_is_deterministic_fresh_prefix_stable_and_rng_pure(native, seed):
    before = random.getstate()
    all_train, all_test = native.sample_inputs(seed, demos=6, queries=4)
    train, test = native.sample_inputs(seed, demos=3, queries=2)
    assert random.getstate() == before
    assert train == all_train[:3]
    assert test == all_test[:2]
    train[0][0][0] = 9
    assert native.sample_inputs(seed, demos=3, queries=2) == (all_train[:3], all_test[:2])
    combined = all_train + all_test
    assert len({json.dumps(grid) for grid in combined}) == len(combined)


@pytest.mark.parametrize("seed", [0, 17])
def test_every_supported_setting_uses_identical_inputs_and_independent_labels(native, seed):
    episodes = {
        scope: native.generate(seed, {"frame_scope": scope}, demos=3, queries=4)
        for scope in ("deepest", "all_seeded")
    }
    assert [p["input"] for p in episodes["deepest"]["train"]] == [p["input"] for p in episodes["all_seeded"]["train"]]
    assert [p["input"] for p in episodes["deepest"]["test"]] == [p["input"] for p in episodes["all_seeded"]["test"]]
    for scope, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == _oracle(pair["input"], scope)
    for pair_deep, pair_all in zip(episodes["deepest"]["train"], episodes["all_seeded"]["train"]):
        assert pair_deep["output"] != pair_all["output"]


def test_large_query_is_substantive_30x30_and_exposes_wrong_intermediate(native):
    _, tests = native.sample_inputs(17, demos=3, queries=4)
    grid = tests[-1]
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 100
    assert max(r for r, _ in nonzero) - min(r for r, _ in nonzero) >= 25
    assert max(c for _, c in nonzero) - min(c for _, c in nonzero) >= 25
    assert _oracle(grid, "deepest") != _oracle(grid, "all_seeded")
