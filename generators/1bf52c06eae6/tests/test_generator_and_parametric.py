"""Regression and native-family tests for 1bf52c06eae6."""
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


TASK_ID = "1bf52c06eae6"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "51585a1368ca51b2e7f9dbc7209a7fa3bf869b44e8c45e673a8c15523fc1327d"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("test_1bf52c06eae6_generator", HOME / "generator.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_1bf52c06eae6_family", PARAM / "family.py")


@pytest.fixture(scope="module")
def adapter():
    return _load("test_1bf52c06eae6_adapter", PARAM / "adapter.py")


def _cells_by_color(grid, *, exclude=()):
    result = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color and color not in exclude:
                result.setdefault(color, []).append((row, col))
    return result


def _boxes(grid, *, exclude=()):
    height, width = len(grid), len(grid[0])
    result = []
    for color, cells in sorted(_cells_by_color(grid, exclude=exclude).items()):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
        side = max(r2 - r1 + 1, c2 - c1 + 1)
        result.append((side * side, color, r1, c1,
                       min(height - 1, r1 + side - 1),
                       min(width - 1, c1 + side - 1)))
    return sorted(result)


def _inside(box, row, col):
    return box[2] <= row <= box[4] and box[3] <= col <= box[5]


def _render(grid, boxes):
    output = [[0 for _ in row] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            hit = next((box for box in boxes if _inside(box, row, col)), None)
            if hit:
                output[row][col] = hit[1]
    return output


def _canonical_reference(grid):
    return _render(grid, _boxes(grid))


def _selected_color(grid):
    probe = _cells_by_color(grid)[9]
    assert len(probe) == 1
    row, col = probe[0]
    boxes = _boxes(grid, exclude={9})
    selected = next(box for box in boxes if _inside(box, row, col))
    return selected[1]


def _probe_demote_reference(grid):
    boxes = _boxes(grid, exclude={9})
    selected = _selected_color(grid)
    ordered = [box for box in boxes if box[1] != selected]
    ordered.extend(box for box in boxes if box[1] == selected)
    return _render(grid, ordered)


def _pairs(episode):
    return episode["train"] + episode["test"]


def _side_areas(grid):
    return [box[0] for box in _boxes(grid)]


@pytest.mark.parametrize("n_colors", [2, 3, 4])
def test_base_n_colors_and_dimensions_are_real(generator, n_colors):
    grid = generator.generate(
        7, n_colors, difficulty="medium", grid_h=10, grid_w=14,
        n_colors=n_colors, palette_kind="broad", density_a=0.35,
        density_b=0.55, position_bias="scattered", anchor_corner=False,
    )
    assert (len(grid), len(grid[0])) == (10, 14)
    assert len(_cells_by_color(grid)) == n_colors
    assert len(_side_areas(grid)) == len(set(_side_areas(grid))) == n_colors
    assert generator.self_check(grid, difficulty="medium") == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": True},
        {"grid_w": 99},
        {"n_colors": 5},
        {"palette_kind": "bad"},
        {"density_a": True},
        {"density_b": 2.0},
        {"position_bias": "bad"},
        {"anchor_corner": 1},
        {"unknown_axis": 1},
        {"texture": "corners", "position_bias": "spread"},
    ],
)
def test_base_invalid_controls_fail_closed(generator, kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(1, 0, **kwargs)


def test_default_program_is_exact_canonical(adapter):
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"priority_mode": "smallest_first"}) == canonical
    assert adapter.program({"priority_mode": "probe_demote"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"priority_mode": "bad"}, {"priority_mode": 1},
     {"priority_mode": "smallest_first", "extra": 1}],
)
def test_settings_surface_is_exact(adapter, settings):
    with pytest.raises(ValueError, match="priority_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_shared_inputs_and_teaching(adapter, family, demos):
    canonical = adapter.generate(17, {"priority_mode": "smallest_first"}, demos, 4)
    probed = adapter.generate(17, {"priority_mode": "probe_demote"}, demos, 4)
    assert len(canonical["train"]) == len(probed["train"]) == demos
    assert len(canonical["test"]) == len(probed["test"]) == 4
    assert [pair["input"] for pair in _pairs(canonical)] == [pair["input"] for pair in _pairs(probed)]
    assert all(a["output"] != b["output"] for a, b in zip(_pairs(canonical), _pairs(probed), strict=True))
    visible = [json.dumps(pair["input"], separators=(",", ":")) for pair in _pairs(canonical)]
    assert len(visible) == len(set(visible)) == demos + 4
    for mode, episode in (("smallest_first", canonical), ("probe_demote", probed)):
        report = family.teaching_report(episode, mode)
        assert report["setting_survivors"] == [mode]
        assert report["surviving_rivals"] == []


def test_labels_match_independent_references_and_probe_varies(adapter):
    canonical = adapter.generate(31, {"priority_mode": "smallest_first"}, 6, 4)
    probed = adapter.generate(31, {"priority_mode": "probe_demote"}, 6, 4)
    selected = []
    selected_ranks = []
    for pair in _pairs(canonical):
        assert pair["output"] == _canonical_reference(pair["input"])
    for pair in _pairs(probed):
        grid = pair["input"]
        assert pair["output"] == _probe_demote_reference(grid)
        color = _selected_color(grid)
        selected.append(color)
        boxes = _boxes(grid, exclude={9})
        selected_ranks.append([box[1] for box in boxes].index(color))
        probe_row, probe_col = _cells_by_color(grid)[9][0]
        covering = [box for box in boxes if _inside(box, probe_row, probe_col)]
        assert len(covering) >= 2
        assert covering[0][1] == color
        assert pair["output"][probe_row][probe_col] != color
    assert len(set(selected)) >= 4
    assert len(set(selected_ranks)) >= 3
    assert any(rank > 0 for rank in selected_ranks)


def test_determinism_fresh_returns_and_global_rng_isolation(adapter):
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(123, {"priority_mode": "probe_demote"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"priority_mode": "probe_demote"}, 3, 4)
    assert before == after
    assert first == second
    changed = copy.deepcopy(first)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"priority_mode": "probe_demote"}, 3, 4) == second


def test_fourth_query_is_substantive_30_by_30(adapter):
    pair = adapter.generate(0, {"priority_mode": "probe_demote"}, 3, 4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 100
    assert len(_cells_by_color(grid, exclude={9})) == 4
    assert len(_cells_by_color(grid)[9]) == 1
    assert any(grid[row][col] != 0 for row, col in ((0, 0), (0, 29), (29, 0), (29, 29)))
    assert pair["output"] == _probe_demote_reference(grid)


def test_promotion_contract_declares_supported_surface():
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"priority_mode": ["smallest_first", "probe_demote"]},
        "default": {"priority_mode": "smallest_first"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/probe_demote.rkt",
        ],
    }
