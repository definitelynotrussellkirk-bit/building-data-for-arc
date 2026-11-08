"""Behavioral checks for the task-local parametric adapter.

These use Python claims only. Native qualification independently replays Racket.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))
PARAMETRIC = HOME / "workspace/parametric"


def load(name):
    path = PARAMETRIC / (name + ".py")
    assert path.is_file(), f"Missing required parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location("test_component_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def areas(grid, color, connectivity=4):
    """Independent set flood fill used to check generated geometry."""
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    result = []
    moves = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (connectivity == 8 or abs(dr) + abs(dc) == 1)]
    while pending:
        stack = [pending.pop()]
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in moves:
                q = (r + dr, c + dc)
                if q in pending:
                    pending.remove(q)
                    stack.append(q)
        result.append(size)
    return sorted(result)


def independent_output(grid, mode):
    by_color = [areas(grid, c) for c in (1, 2, 3)]
    k = len(by_color[0])
    counts = [len(a) if mode == "all" else sum(size >= k for size in a) for a in by_color]
    width = max(1, *counts)
    return [[color if j < n else 0 for j in range(width)]
            for color, n in zip((1, 2, 3), counts)]


def inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_selected_canonical_program_is_byte_exact():
    from arcpuzzles import Catalog
    adapter = load("adapter")
    selected = Catalog(ROOT)._variants()["dc91f4798e24"][0]["program_solution"]
    assert adapter.program({"mode": "all"}) == selected
    assert adapter.program({"mode": "blue_count_threshold"}) != selected


def test_rule_uses_blue_component_count_before_filtering():
    prototype = load("prototype")
    grid = [[int(x) for x in row] for row in (
        "11200330", "00110000", "00000000", "20000330",
        "00000300", "22000004", "20000044")]
    assert prototype.solve(grid, "all") == [[1, 1, 0], [2, 2, 2], [3, 3, 0]]
    assert prototype.solve(grid, "blue_count_threshold") == [[1, 1], [2, 0], [3, 3]]
    assert sorted(map(len, prototype.components(grid, 1))) == [2, 2]
    assert sorted(map(len, prototype.components(grid, 1, 8))) == [4]


def test_empty_target_histogram_has_one_column():
    prototype = load("prototype")
    assert prototype.solve([[0, 4], [5, 0]], "all") == [[0], [0], [0]]
    assert prototype.solve([[0, 4], [5, 0]], "blue_count_threshold") == [[0], [0], [0]]
    assert prototype.bars([0, 0, 0]) == [[0], [0], [0]]


@pytest.mark.parametrize("seed", [0, 17, 61, 2026])
def test_matched_inputs_reproducibility_and_independent_labels(seed):
    adapter = load("adapter")
    canonical = adapter.generate(seed, {"mode": "all"}, demos=3, queries=4)
    alternate = adapter.generate(seed, {"mode": "blue_count_threshold"}, demos=3, queries=4)
    assert canonical == adapter.generate(seed, {"mode": "all"}, demos=3, queries=4)
    assert inputs(canonical, "train") == inputs(alternate, "train")
    assert inputs(canonical, "test") == inputs(alternate, "test")
    for mode, episode in (("all", canonical), ("blue_count_threshold", alternate)):
        assert episode["program_solution"] == adapter.program({"mode": mode})
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == independent_output(pair["input"], mode)
            assert all(type(v) is int and 0 <= v <= 9 for row in pair["input"] for v in row)
    assert canonical["train"][0]["output"] != alternate["train"][0]["output"]


def test_demo_query_counts_are_independent_with_stable_prefixes():
    adapter = load("adapter")
    settings = {"mode": "blue_count_threshold"}
    full = adapter.generate(17, settings, demos=6, queries=4)
    for demos, queries in ((2, 1), (2, 4), (3, 2), (4, 3), (5, 1), (6, 4)):
        part = adapter.generate(17, settings, demos=demos, queries=queries)
        assert part["train"] == full["train"][:demos]
        assert part["test"] == full["test"][:queries]
    default = adapter.generate(17, settings)
    assert len(default["train"]) == 3
    assert len(default["test"]) == 4


@pytest.mark.parametrize("seed", [0, 17, 61, 2026])
def test_minimum_demos_refute_declared_finite_rivals(seed):
    adapter, prototype = load("adapter"), load("prototype")
    for mode in ("all", "blue_count_threshold"):
        episode = adapter.generate(seed, {"mode": mode}, demos=2, queries=1)
        rows = [prototype.rival_outputs(p["input"], mode) for p in episode["train"]]
        assert set(rows[0]) == set(rows[1])
        survivors = [name for name in rows[0]
                     if all(rivals[name] == pair["output"]
                            for rivals, pair in zip(rows, episode["train"]))]
        assert survivors == []
        assert all(len(areas(p["input"], 1)) >= 2 for p in episode["train"])


@pytest.mark.parametrize("seed", [0, 17, 61, 2026])
def test_query_geometry_spans_envelope_and_large_grid_is_substantive(seed):
    episode = load("adapter").generate(seed, {"mode": "blue_count_threshold"}, demos=6, queries=4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
        (7, 8), (12, 16), (24, 24), (30, 30)]
    encoded = [json.dumps(p["input"]) for p in episode["train"] + episode["test"]]
    assert len(set(encoded)) == 10
    grid = episode["test"][-1]["input"]
    assert sum(len(areas(grid, c)) for c in (1, 2, 3)) >= 40
    assert sum(v != 0 for row in grid for v in row) >= 225
    assert sum(v >= 4 for row in grid for v in row) >= 24
    assert all(any(v in (1, 2, 3) for v in edge) for edge in (
        grid[0], grid[-1], [row[0] for row in grid], [row[-1] for row in grid]))
    for rows in (grid[:15], grid[15:]):
        for start in (0, 15):
            assert sum(v in (1, 2, 3) for row in rows for v in row[start:start+15]) >= 25


def test_grid_stats_describe_actual_input():
    prototype = load("prototype")
    grid = [[1, 2, 0], [0, 1, 4], [3, 0, 0]]
    stats = prototype.grid_stats(grid)
    assert stats["height"] == stats["width"] == 3
    assert stats["counts4"] == [2, 1, 1]
    assert stats["counts8"] == [1, 1, 1]
    assert stats["threshold"] == 2
    assert stats["areas"] == {"1": [1, 1], "2": [1], "3": [1]}
    assert stats["eligible_counts"] == [0, 0, 0]
    assert stats["foreground_cells"] == 5
    assert stats["distractor_cells"] == 1
    json.dumps(stats)


@pytest.mark.parametrize("settings", [None, {}, {"mode": "bad"}, {"mode": True},
                                      {"mode": ["all"]}, {"mode": "all", "extra": 1},
                                      "all", ["all"]])
def test_rejects_malformed_settings(settings):
    adapter = load("adapter")
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings)


@pytest.mark.parametrize("name,bad", [("seed", True), ("seed", -1), ("seed", 2**63),
                                     ("seed", "0"), ("seed", 0.0), ("seed", None),
                                     ("demos", True), ("demos", 1), ("demos", 7),
                                     ("demos", 3.0), ("demos", "3"), ("demos", None),
                                     ("queries", False), ("queries", 0), ("queries", 5),
                                     ("queries", 1.0), ("queries", "1"), ("queries", None)])
def test_rejects_invalid_request_primitive_types_and_ranges(name, bad):
    kwargs = {"seed": 0, "settings": {"mode": "all"}, "demos": 2, "queries": 1}
    kwargs[name] = bad
    with pytest.raises(ValueError):
        load("adapter").generate(**kwargs)


@pytest.mark.parametrize("grid", [[], [[]], [[1], [1, 2]], [[True]], [[-1]], [[10]], [[1.0]], ["1"]])
def test_analysis_rejects_invalid_grids(grid):
    prototype = load("prototype")
    with pytest.raises(ValueError):
        prototype.solve(grid)


def test_rejects_invalid_component_primitive_arguments():
    prototype = load("prototype")
    for color in (True, -1, 10, "1", 1.0):
        with pytest.raises(ValueError):
            prototype.components([[1]], color)
    for connectivity in (True, 0, 6, "4", 4.0):
        with pytest.raises(ValueError):
            prototype.components([[1]], 1, connectivity)


def test_promotion_contract_can_describe_native_requests():
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"mode": ["all", "blue_count_threshold"]}
    assert contract["default"] == {"mode": "all"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert (ROOT / contract["adapter"]).is_file()

