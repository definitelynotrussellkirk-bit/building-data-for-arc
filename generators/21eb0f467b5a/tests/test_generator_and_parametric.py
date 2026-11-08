"""Regression and native-family tests for 21eb0f467b5a."""
from __future__ import annotations

import copy
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "21eb0f467b5a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "a67351f37a49020c656adf08bd4566d328af5fe97acad3e510012b9868fe9449"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("test_21eb0f467b5a_generator", HOME / "generator.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_21eb0f467b5a_family", PARAM / "family.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("test_21eb0f467b5a_adapter", PARAM / "adapter.py")


def _cells_by_color(grid):
    cells = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                cells[color].append((row, col))
    return dict(cells)


def _pair_signature(cells):
    if len(cells) != 2:
        return None
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        return ("horizontal", abs(c2 - c1) + 1)
    if c1 == c2:
        return ("vertical", abs(r2 - r1) + 1)
    return ("diagonal", None)


def _paint_segment(output, color, cells):
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        for col in range(min(c1, c2), max(c1, c2) + 1):
            output[r1][col] = color
    elif c1 == c2:
        for row in range(min(r1, r2), max(r1, r2) + 1):
            output[row][c1] = color
    else:
        for row, col in cells:
            output[row][col] = color


def _canonical_reference(grid):
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(_cells_by_color(grid).items()):
        if len(cells) == 2:
            _paint_segment(output, color, cells)
        else:
            for row, col in cells:
                output[row][col] = color
    return output


def _key_reference(grid):
    by_color = _cells_by_color(grid)
    key = _pair_signature(by_color[7])
    assert key is not None and key[0] in {"horizontal", "vertical"}
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(by_color.items()):
        signature = _pair_signature(cells)
        if len(cells) != 2:
            for row, col in cells:
                output[row][col] = color
        elif color == 7 or signature == key:
            _paint_segment(output, color, cells)
        else:
            for row, col in cells:
                output[row][col] = color
    return output


def _pairs(episode):
    return episode["train"] + episode["test"]


def test_base_declared_controls_are_real(generator):
    row = generator.generate(
        0, 0, difficulty="medium", grid_h=8, grid_w=12,
        alignment="row", palette_kind="warm", palette_size=2,
        n_distinct_colors=2, position_bias="aligned_pair_plus_singleton",
        density="sparse",
    )
    col = generator.generate(
        0, 0, difficulty="medium", grid_h=9, grid_w=11,
        alignment="col", palette_kind="cool", palette_size=2,
        n_distinct_colors=2, position_bias="aligned_pair_plus_singleton",
        density="sparse",
    )
    assert (len(row), len(row[0])) == (8, 12)
    assert (len(col), len(col[0])) == (9, 11)
    row_signatures = [_pair_signature(cells) for cells in _cells_by_color(row).values()]
    col_signatures = [_pair_signature(cells) for cells in _cells_by_color(col).values()]
    assert any(sig and sig[0] == "horizontal" for sig in row_signatures)
    assert any(sig and sig[0] == "vertical" for sig in col_signatures)
    assert generator.self_check(row, difficulty="medium") == []
    assert generator.self_check(col, difficulty="medium") == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": True},
        {"grid_w": 99},
        {"alignment": "diagonal"},
        {"palette_size": 3},
        {"n_distinct_colors": 1},
        {"unknown_axis": 1},
        {"texture": "warm", "palette_kind": "cool"},
    ],
)
def test_base_invalid_controls_fail_closed(generator, kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(1, 0, **kwargs)


def test_default_program_is_exact_canonical(adapter):
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"connection_mode": "all_aligned"}) == canonical
    assert adapter.program({"connection_mode": "key_match"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"connection_mode": "bad"}, {"connection_mode": 1},
     {"connection_mode": "all_aligned", "extra": 1}],
)
def test_settings_surface_is_exact(adapter, settings):
    with pytest.raises(ValueError, match="connection_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_shared_inputs_and_teaching(adapter, family, demos):
    canonical = adapter.generate(17, {"connection_mode": "all_aligned"}, demos, 4)
    keyed = adapter.generate(17, {"connection_mode": "key_match"}, demos, 4)
    assert len(canonical["train"]) == len(keyed["train"]) == demos
    assert len(canonical["test"]) == len(keyed["test"]) == 4
    assert [pair["input"] for pair in _pairs(canonical)] == [pair["input"] for pair in _pairs(keyed)]
    assert all(a["output"] != b["output"] for a, b in zip(_pairs(canonical), _pairs(keyed), strict=True))
    visible = [json.dumps(pair["input"], separators=(",", ":")) for pair in _pairs(canonical)]
    assert len(visible) == len(set(visible)) == demos + 4
    for mode, episode in (("all_aligned", canonical), ("key_match", keyed)):
        report = family.teaching_report(episode, mode)
        assert report["setting_survivors"] == [mode]
        assert report["surviving_rivals"] == []


def test_labels_match_independent_references_and_key_varies(adapter):
    canonical = adapter.generate(31, {"connection_mode": "all_aligned"}, 6, 4)
    keyed = adapter.generate(31, {"connection_mode": "key_match"}, 6, 4)
    signatures = []
    for pair in _pairs(canonical):
        assert pair["output"] == _canonical_reference(pair["input"])
    for pair in _pairs(keyed):
        assert pair["output"] == _key_reference(pair["input"])
        signature = _pair_signature(_cells_by_color(pair["input"])[7])
        signatures.append(signature)
        others = [
            _pair_signature(cells)
            for color, cells in _cells_by_color(pair["input"]).items()
            if color not in {7, 9}
        ]
        assert signature in others
        assert any(value and value[0] == signature[0] and value[1] != signature[1] for value in others)
        assert any(value and value[0] != signature[0] and value[1] == signature[1] for value in others)
    assert len(set(signatures)) >= 4
    assert {orientation for orientation, _ in signatures} == {"horizontal", "vertical"}


def test_determinism_fresh_returns_and_global_rng_isolation(adapter):
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(123, {"connection_mode": "key_match"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"connection_mode": "key_match"}, 3, 4)
    assert before == after
    assert first == second
    changed = copy.deepcopy(first)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"connection_mode": "key_match"}, 3, 4) == second


def test_fourth_query_is_substantive_30_by_30(adapter):
    pair = adapter.generate(0, {"connection_mode": "key_match"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 90
    assert len(_cells_by_color(grid)) >= 8
    assert any(grid[r][c] != 0 for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))
    assert pair["output"] == _key_reference(grid)


def test_promotion_contract_declares_supported_surface():
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"connection_mode": ["all_aligned", "key_match"]},
        "default": {"connection_mode": "all_aligned"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/key_match.rkt",
        ],
    }
