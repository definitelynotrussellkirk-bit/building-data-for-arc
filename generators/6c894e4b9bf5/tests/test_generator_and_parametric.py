"""Regression and native-family tests for 6c894e4b9bf5."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "6c894e4b9bf5"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "515f38b644886715e18d30597fc02a73438faab3dae7daeb7d91a124f998edd5"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("test_6c894e4b9bf5_generator", HOME / "generator.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_6c894e4b9bf5_family", PARAM / "family.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("test_6c894e4b9bf5_adapter", PARAM / "adapter.py")


def _components(grid, color):
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in todo:
                    todo.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        result.append(cells)
    return result


def _is_vertical(cells):
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return len(cells) >= 2 and len(cols) == 1 and len(rows) == max(rows) - min(rows) + 1


def _canonical_reference(grid):
    out = [row[:] for row in grid]
    for cells in _components(grid, 2):
        if not _is_vertical(cells):
            continue
        col = next(iter(c for _, c in cells))
        rows = sorted(r for r, _ in cells)
        out[rows[0]][col] = 1
        out[rows[-1]][col] = 1
    return out


def _ruler_reference(grid):
    rulers = [cells for cells in _components(grid, 7) if _is_vertical(cells)]
    assert len(rulers) == 1
    threshold = len(rulers[0])
    out = [row[:] for row in grid]
    for cells in _components(grid, 2):
        if not _is_vertical(cells) or len(cells) < threshold:
            continue
        col = next(iter(c for _, c in cells))
        rows = sorted(r for r, _ in cells)
        out[rows[0]][col] = 1
        out[rows[-1]][col] = 1
    return out


def _pairs(episode):
    return episode["train"] + episode["test"]


def test_base_n_lines_override_is_observed(generator):
    three = generator.generate(0, 0, difficulty="medium", n_lines=3)
    four = generator.generate(0, 0, difficulty="medium", n_lines=4)
    assert sum(_is_vertical(c) for c in _components(three, 2)) == 3
    assert sum(_is_vertical(c) for c in _components(four, 2)) == 4
    assert three != four


def test_base_normal_draws_teach_the_negative_shape_branch(generator):
    for seed in range(12):
        grid = generator.generate(seed, 0, difficulty="medium")
        comps = _components(grid, 2)
        assert generator.self_check(grid, difficulty="medium") == []
        assert any(_is_vertical(c) for c in comps)
        assert any(not _is_vertical(c) for c in comps)
        output = _canonical_reference(grid)
        for cells in comps:
            if not _is_vertical(cells):
                assert all(output[r][c] == 2 for r, c in cells)


def test_default_program_is_exact_canonical(adapter):
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"selection_mode": "all_vertical"}) == canonical
    assert adapter.program({"selection_mode": "ruler_threshold"}) != canonical


@pytest.mark.parametrize("settings", [None, {}, {"selection_mode": "bad"}, {"selection_mode": 1}, {"selection_mode": "all_vertical", "x": 1}])
def test_settings_surface_is_exact(adapter, settings):
    with pytest.raises(ValueError, match="selection_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_shared_inputs_and_setting_separation(adapter, demos):
    canonical = adapter.generate(17, {"selection_mode": "all_vertical"}, demos, 4)
    threshold = adapter.generate(17, {"selection_mode": "ruler_threshold"}, demos, 4)
    assert len(canonical["train"]) == len(threshold["train"]) == demos
    assert len(canonical["test"]) == len(threshold["test"]) == 4
    assert [p["input"] for p in _pairs(canonical)] == [p["input"] for p in _pairs(threshold)]
    assert all(a["output"] != b["output"] for a, b in zip(_pairs(canonical), _pairs(threshold), strict=True))
    serialized = [json.dumps(p["input"], separators=(",", ":")) for p in _pairs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4


def test_labels_match_independent_references_and_threshold_varies(adapter):
    all_episode = adapter.generate(31, {"selection_mode": "all_vertical"}, 6, 4)
    threshold_episode = adapter.generate(31, {"selection_mode": "ruler_threshold"}, 6, 4)
    thresholds = []
    for pair in _pairs(all_episode):
        assert pair["output"] == _canonical_reference(pair["input"])
    for pair in _pairs(threshold_episode):
        assert pair["output"] == _ruler_reference(pair["input"])
        rulers = [c for c in _components(pair["input"], 7) if _is_vertical(c)]
        thresholds.append(len(rulers[0]))
        lengths = sorted(len(c) for c in _components(pair["input"], 2) if _is_vertical(c))
        assert any(length < thresholds[-1] for length in lengths)
        assert any(length == thresholds[-1] for length in lengths)
        assert any(length > thresholds[-1] for length in lengths)
    assert len(set(thresholds)) >= 3


def test_determinism_and_random_state(adapter):
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(123, {"selection_mode": "ruler_threshold"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"selection_mode": "ruler_threshold"}, 3, 4)
    assert before == after
    assert first == second
    mutated = copy.deepcopy(first)
    mutated["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"selection_mode": "ruler_threshold"}, 3, 4) == second


def test_fourth_query_is_substantive_30_by_30(adapter):
    pair = adapter.generate(0, {"selection_mode": "ruler_threshold"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 70
    assert len(_components(grid, 2)) >= 10
    assert any(grid[r][c] != 0 for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))


def test_promotion_contract_declares_supported_surface():
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"selection_mode": ["all_vertical", "ruler_threshold"]},
        "default": {"selection_mode": "all_vertical"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/ruler_threshold.rkt",
        ],
    }
