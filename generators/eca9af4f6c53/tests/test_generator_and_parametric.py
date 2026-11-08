"""Regression and native-family tests for eca9af4f6c53."""
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


TASK_ID = "eca9af4f6c53"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "64ed10ee03ea164e401a87fd720803b3989f14a01f3c0756f69ef8e8ae231530"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("test_eca9af4f6c53_generator", HOME / "generator.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_eca9af4f6c53_family", PARAM / "family.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("test_eca9af4f6c53_adapter", PARAM / "adapter.py")


def _pairs(episode):
    return episode["train"] + episode["test"]


def _colors(grid):
    return {v for row in grid for v in row if v != 0}


def _global_reference(grid):
    out = [row[:] for row in grid]
    for color in sorted(_colors(grid)):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if (len(cells) == 3 and len(rows) == 2 and len(cols) == 2
                and rows[1] - rows[0] == 1 and cols[1] - cols[0] == 1):
            for r in rows:
                for c in cols:
                    out[r][c] = color
    return out


def _local_pass(grid):
    h, w = len(grid), len(grid[0])
    writes = {}
    for r0 in range(h - 1):
        for c0 in range(w - 1):
            cells = [(r, c, grid[r][c]) for r in (r0, r0 + 1) for c in (c0, c0 + 1)]
            nonzero = [v for _, _, v in cells if v != 0]
            zeros = [(r, c) for r, c, v in cells if v == 0]
            if len(zeros) == 1 and len(nonzero) == 3 and len(set(nonzero)) == 1:
                cell = zeros[0]
                color = nonzero[0]
                assert cell not in writes or writes[cell] == color
                writes[cell] = color
    out = [row[:] for row in grid]
    for (r, c), color in sorted(writes.items()):
        out[r][c] = color
    return out


def _two_pass_reference(grid):
    return _local_pass(_local_pass(grid))


def test_base_count_controls_are_observed_and_must_agree(generator):
    one = generator.generate(0, 0, difficulty="medium", n_blocks=1, palette_size=1, n_distinct_colors=1)
    six = generator.generate(0, 0, difficulty="medium", n_blocks=6, palette_size=6, n_distinct_colors=6)
    assert len(_colors(one)) == 1
    assert len(_colors(six)) == 6
    assert generator.self_check(one, difficulty="medium") == []
    assert generator.self_check(six, difficulty="medium") == []
    with pytest.raises(ValueError, match="must agree"):
        generator.generate(0, 0, n_blocks=3, palette_size=2)


def test_base_normal_draws_remain_valid(generator):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(12):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            assert 1 <= len(_colors(grid)) <= 9


def test_default_program_is_exact_canonical(adapter):
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"completion_mode": "global_color"}) == canonical
    assert adapter.program({"completion_mode": "two_pass_local"}) != canonical


@pytest.mark.parametrize("settings", [None, {}, {"completion_mode": "bad"}, {"completion_mode": 1}, {"completion_mode": "global_color", "x": 1}])
def test_settings_surface_is_exact(adapter, settings):
    with pytest.raises(ValueError, match="completion_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_shared_inputs_and_setting_separation(adapter, demos):
    global_ep = adapter.generate(17, {"completion_mode": "global_color"}, demos, 4)
    local_ep = adapter.generate(17, {"completion_mode": "two_pass_local"}, demos, 4)
    assert len(global_ep["train"]) == len(local_ep["train"]) == demos
    assert len(global_ep["test"]) == len(local_ep["test"]) == 4
    assert [p["input"] for p in _pairs(global_ep)] == [p["input"] for p in _pairs(local_ep)]
    assert all(a["output"] != b["output"] for a, b in zip(_pairs(global_ep), _pairs(local_ep), strict=True))
    serialized = [json.dumps(p["input"], separators=(",", ":")) for p in _pairs(global_ep)]
    assert len(serialized) == len(set(serialized)) == demos + 4


def test_labels_match_independent_references_and_require_exactly_two_passes(adapter):
    global_ep = adapter.generate(31, {"completion_mode": "global_color"}, 6, 4)
    local_ep = adapter.generate(31, {"completion_mode": "two_pass_local"}, 6, 4)
    for pair in _pairs(global_ep):
        assert pair["output"] == _global_reference(pair["input"])
    for pair in _pairs(local_ep):
        first = _local_pass(pair["input"])
        second = _local_pass(first)
        third = _local_pass(second)
        assert pair["output"] == second == _two_pass_reference(pair["input"])
        assert first != second
        assert second != third


def test_determinism_and_random_state(adapter):
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(123, {"completion_mode": "two_pass_local"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"completion_mode": "two_pass_local"}, 3, 4)
    assert before == after
    assert first == second
    mutated = copy.deepcopy(first)
    mutated["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"completion_mode": "two_pass_local"}, 3, 4) == second


def test_fourth_query_is_substantive_30_by_30(adapter):
    pair = adapter.generate(0, {"completion_mode": "two_pass_local"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 120
    assert sum(a != b for ra, rb in zip(grid, pair["output"], strict=True) for a, b in zip(ra, rb, strict=True)) >= 20
    assert any(grid[r][c] != 0 for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))


def test_promotion_contract_declares_supported_surface():
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"completion_mode": ["global_color", "two_pass_local"]},
        "default": {"completion_mode": "global_color"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/two_pass_local.rkt",
        ],
    }
