"""Native contract for compass-fixed versus arm-area-ranked color assignment."""
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


TASK_ID = "08f1d9bdd2ef"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
CANONICAL_SHA256 = "f6b3997cccd5000fd3dbdc752aba58d002f1b2d4d4380c21fdaae2b58a3b5af5"
DIRECTIONS = ("top", "right", "bottom", "left")
RANK_COLORS = (2, 3, 1, 4)


def _load(name: str, filename: str):
    path = HOME / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("test_08f1_area_adapter", "adapter.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_08f1_area_family", "area_ranked.py")


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _facts(grid):
    height, width = len(grid), len(grid[0])
    rows = [r for r in range(height) if all(grid[r][c] == 8 for c in range(width))]
    cols = [c for c in range(width) if all(grid[r][c] == 8 for r in range(height))]
    assert len(rows) == len(cols) == 2
    row_sizes = (rows[0], rows[1] - rows[0] - 1, height - rows[1] - 1)
    col_sizes = (cols[0], cols[1] - cols[0] - 1, width - cols[1] - 1)
    areas = {
        "top": row_sizes[0] * col_sizes[1],
        "right": row_sizes[1] * col_sizes[2],
        "bottom": row_sizes[2] * col_sizes[1],
        "left": row_sizes[1] * col_sizes[0],
    }
    ranking = tuple(sorted(DIRECTIONS, key=lambda name: (-areas[name], DIRECTIONS.index(name))))
    return rows, cols, row_sizes, col_sizes, areas, ranking


def _reference(grid, mode):
    height, width = len(grid), len(grid[0])
    rows, cols, _, _, _, ranking = _facts(grid)
    if mode == "compass":
        colors = {"top": 2, "right": 3, "bottom": 1, "left": 4}
    else:
        colors = dict(zip(ranking, RANK_COLORS, strict=True))
    out = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if row in rows or col in cols:
                out[row][col] = 8
                continue
            rb = int(row > rows[0]) + int(row > rows[1])
            cb = int(col > cols[0]) + int(col > cols[1])
            direction = {
                (0, 1): "top",
                (1, 2): "right",
                (2, 1): "bottom",
                (1, 0): "left",
            }.get((rb, cb))
            out[row][col] = 6 if (rb, cb) == (1, 1) else colors.get(direction, 0)
    return out


def test_default_program_is_exact_selected_canonical_source(adapter):
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"arm_assignment": "compass"}) == canonical
    assert adapter.program({"arm_assignment": "area_ranked"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"arm_assignment": "compass", "extra": 1}, {"arm_assignment": "bad"}, {"arm_assignment": 1}],
)
def test_settings_are_exact_and_finite(adapter, settings):
    with pytest.raises(ValueError, match="arm_assignment"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "0", None])
def test_seed_is_nonnegative_plain_integer(adapter, bad):
    with pytest.raises(ValueError, match="seed"):
        adapter.generate(bad, {"arm_assignment": "compass"}, 3, 4)


@pytest.mark.parametrize("bad", [True, False, 1, 7, 2.5, "3", None])
def test_demo_count_is_two_through_six(adapter, bad):
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"arm_assignment": "compass"}, bad, 4)


@pytest.mark.parametrize("bad", [True, False, 0, 1, 3, 5, 4.0, "4", None])
def test_query_count_is_exactly_four(adapter, bad):
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"arm_assignment": "compass"}, 3, bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_matched_inputs_and_setting_identification(adapter, demos):
    compass = adapter.generate(17, {"arm_assignment": "compass"}, demos, 4)
    ranked = adapter.generate(17, {"arm_assignment": "area_ranked"}, demos, 4)
    assert len(compass["train"]) == len(ranked["train"]) == demos
    assert len(compass["test"]) == len(ranked["test"]) == 4
    assert _inputs(compass) == _inputs(ranked)
    keys = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(compass)]
    assert len(keys) == len(set(keys)) == demos + 4
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(compass), _pairs(ranked), strict=True)
    )


def test_claimed_labels_match_independent_geometry_and_ranking(adapter):
    for mode in ("compass", "area_ranked"):
        episode = adapter.generate(31, {"arm_assignment": mode}, 6, 4)
        for pair in _pairs(episode):
            assert pair["output"] == _reference(pair["input"], mode)


def test_intermediate_is_input_derived_unique_and_varied(family, adapter):
    episode = adapter.generate(29, {"arm_assignment": "area_ranked"}, 6, 4)
    rankings = []
    for pair in _pairs(episode):
        rows, cols, row_sizes, col_sizes, areas, ranking = _facts(pair["input"])
        intermediate = family.dependency_intermediate(pair["input"])
        assert intermediate == {
            "separator_rows": rows,
            "separator_cols": cols,
            "row_band_sizes": row_sizes,
            "col_band_sizes": col_sizes,
            "arm_areas": areas,
            "area_ranking": ranking,
        }
        assert len(set(areas.values())) == 4
        assert ranking != DIRECTIONS
        rankings.append(ranking)
    assert len(set(rankings)) >= 6


def test_determinism_freshness_and_global_rng_purity(adapter):
    random.seed(1191)
    before = random.getstate()
    first = adapter.generate(123, {"arm_assignment": "area_ranked"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"arm_assignment": "area_ranked"}, 3, 4)
    assert before == after
    assert first == second
    changed = copy.deepcopy(first)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"arm_assignment": "area_ranked"}, 3, 4) == second


def test_fourth_query_is_substantive_30_by_30_with_rank_reassignment(adapter):
    compass = adapter.generate(0, {"arm_assignment": "compass"}, 3, 4)["test"][3]
    ranked = adapter.generate(0, {"arm_assignment": "area_ranked"}, 3, 4)["test"][3]
    grid = compass["input"]
    assert grid == ranked["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    _, _, _, _, areas, ranking = _facts(grid)
    assert len(set(areas.values())) == 4
    assert ranking != DIRECTIONS
    assert sum(value != 0 for row in ranked["output"] for value in row) >= 500
    assert compass["output"] != ranked["output"]


def test_promotion_contract_declares_only_supported_surface():
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"arm_assignment": ["compass", "area_ranked"]},
        "default": {"arm_assignment": "compass"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/area_ranked.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }
