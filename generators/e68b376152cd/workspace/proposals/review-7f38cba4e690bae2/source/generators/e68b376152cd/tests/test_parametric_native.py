"""Behavior tests for the native left-to-right versus area-descending gallery family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from collections import deque
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/e68b376152cd"
NATIVE = HOME / "workspace/parametric/native.py"


def _load_native():
    if not NATIVE.is_file():
        pytest.fail("native parametric implementation is missing")
    spec = importlib.util.spec_from_file_location("native_e68_under_test", NATIVE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    records = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = rr + dr, cc + dc
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        todo.append(p)
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            records.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "area": len(cells),
            })
    return records


def _crop(record):
    r0, c0, r1, c1 = record["bbox"]
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in record["cells"]:
        out[r - r0][c - c0] = record["color"]
    return out


def _pack(records):
    pieces = [_crop(record) for record in records]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _oracle(grid, order):
    records = _components(grid)
    if order == "left_to_right":
        records.sort(key=lambda rec: (rec["bbox"][1], rec["bbox"][0]))
    elif order == "area_descending":
        records.sort(key=lambda rec: (-rec["area"], rec["bbox"][1], rec["bbox"][0]))
    else:
        raise AssertionError(order)
    return _pack(records)


@pytest.fixture(scope="module")
def native():
    return _load_native()


def test_default_program_is_exact_selected_canonical_bytes(native):
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "e68b376152cd"
    }
    assert programs == {native.program({"object_order": "left_to_right"})}
    canonical = next(iter(programs))
    assert hashlib.sha256(canonical.encode()).hexdigest() == hashlib.sha256(
        (HOME / "workspace/parametric/canonical.rkt").read_bytes()
    ).hexdigest()
    assert native.program({"object_order": "area_descending"}) != canonical


@pytest.mark.parametrize("settings", [
    None, {}, "left_to_right", {"object_order": True}, {"object_order": "other"},
    {"object_order": "left_to_right", "extra": 1},
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
        order: native.generate(seed, {"object_order": order}, demos=3, queries=4)
        for order in ("left_to_right", "area_descending")
    }
    assert [p["input"] for p in episodes["left_to_right"]["train"]] == [p["input"] for p in episodes["area_descending"]["train"]]
    assert [p["input"] for p in episodes["left_to_right"]["test"]] == [p["input"] for p in episodes["area_descending"]["test"]]
    for order, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == _oracle(pair["input"], order)
    for pair_left, pair_area in zip(episodes["left_to_right"]["train"], episodes["area_descending"]["train"]):
        assert pair_left["output"] != pair_area["output"]


def test_large_query_is_substantive_30x30_and_exposes_wrong_order(native):
    _, tests = native.sample_inputs(17, demos=3, queries=4)
    grid = tests[-1]
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 100
    assert max(r for r, _ in nonzero) - min(r for r, _ in nonzero) >= 25
    assert max(c for _, c in nonzero) - min(c for _, c in nonzero) >= 28
    records = _components(grid)
    assert len(records) == 5
    assert len({record["area"] for record in records}) == 5
    assert _oracle(grid, "left_to_right") != _oracle(grid, "area_descending")
