"""Native cell-count versus bbox-area selection family regressions."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "2786bc764238"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "native parametric adapter has not been built"
    name = "_test_2786bc764238_parametric"
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    variants = Catalog(ROOT).get(TASK_ID)["variants"]
    programs = {row["program_solution"] for row in variants}
    assert len(programs) == 1
    return next(iter(programs))


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        result.append({
            "cells": frozenset(cells),
            "size": len(cells),
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
        })
    return result


def _bbox_area(component):
    r1, c1, r2, c2 = component["bbox"]
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _crop(grid, component):
    r1, c1, r2, c2 = component["bbox"]
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _winner(grid, metric):
    components = _components(grid)
    if metric == "cell_count":
        key = lambda c: (-c["size"], c["bbox"][0], c["bbox"][1])
    else:
        key = lambda c: (-_bbox_area(c), c["bbox"][0], c["bbox"][1])
    return sorted(components, key=key)[0]


def _visible_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _serialized(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_default_program_is_exact_canonical_and_bbox_variant_changes_metric_only():
    adapter = _load_adapter()
    canonical = adapter.program({"selection_metric": "cell_count"})
    alternative = adapter.program({"selection_metric": "bbox_area"})
    assert canonical == _canonical_program()
    assert alternative != canonical
    assert "obj-size" in canonical
    assert "bbox-area" in alternative
    assert alternative.startswith("(rule!")


@pytest.mark.parametrize("settings", [
    None, {}, {"selection_metric": "cell_count", "extra": 1},
    {"selection_metric": True}, {"selection_metric": 0},
    {"selection_metric": "width"},
])
def test_settings_validation_is_exact(settings):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 4), (-1, 2, 4), (2**63, 2, 4), (1.0, 2, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 2, True), (0, 2, 3), (0, 2, 5),
])
def test_request_boundaries_are_strict(seed, demos, queries):
    adapter = _load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"selection_metric": "cell_count"}, demos, queries)


@pytest.mark.parametrize("demos", [2, 6])
def test_min_and_max_counts_have_four_distinct_queries(demos):
    adapter = _load_adapter()
    episode = adapter.generate(20261025, {"selection_metric": "bbox_area"}, demos, 4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"selection_metric": "bbox_area"})
    enc = [_serialized(grid) for grid in _visible_inputs(episode)]
    assert len(enc) == len(set(enc))


def test_inputs_are_setting_independent_and_every_demo_distinguishes_metrics():
    adapter = _load_adapter()
    by_cells = adapter.generate(44617, {"selection_metric": "cell_count"}, 2, 4)
    by_bbox = adapter.generate(44617, {"selection_metric": "bbox_area"}, 2, 4)
    assert _visible_inputs(by_cells) == _visible_inputs(by_bbox)
    assert adapter.generate(44617, {"selection_metric": "cell_count"}, 2, 4) == by_cells
    assert all(a["output"] != b["output"] for a, b in zip(by_cells["train"], by_bbox["train"]))


@pytest.mark.parametrize("metric", ["cell_count", "bbox_area"])
def test_every_pair_crops_the_declared_unique_metric_winner(metric):
    adapter = _load_adapter()
    episode = adapter.generate(7001, {"selection_metric": metric}, 3, 4)
    for pair in [*episode["train"], *episode["test"]]:
        components = _components(pair["input"])
        cell_sizes = [c["size"] for c in components]
        bbox_areas = [_bbox_area(c) for c in components]
        assert cell_sizes.count(max(cell_sizes)) == 1
        assert bbox_areas.count(max(bbox_areas)) == 1
        assert _winner(pair["input"], "cell_count")["cells"] != _winner(pair["input"], "bbox_area")["cells"]
        assert pair["output"] == _crop(pair["input"], _winner(pair["input"], metric))


def test_query_bank_contains_lower_boundary_and_substantive_30x30_stress():
    adapter = _load_adapter()
    episode = adapter.generate(99, {"selection_metric": "cell_count"}, 3, 4)
    grids = [pair["input"] for pair in episode["test"]]
    assert (9, 12) in {(len(g), len(g[0])) for g in grids}
    stress = next(g for g in grids if (len(g), len(g[0])) == (30, 30))
    assert sum(value != 0 for row in stress for value in row) >= 140
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 24
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 24
    assert len(_components(stress)) >= 4
