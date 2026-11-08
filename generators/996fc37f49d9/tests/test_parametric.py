from __future__ import annotations

import importlib.util
import json
import random
import sys

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / "996fc37f49d9"
ADAPTER = TASK_HOME / "workspace" / "parametric" / "adapter.py"
SETTINGS = ({"rank_metric": "cells"}, {"rank_metric": "bounding_box"})


def _load():
    assert ADAPTER.is_file(), "parametric adapter has not been implemented"
    name = "test_parametric_996fc37f49d9"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ADAPTER)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _canonical_program() -> str:
    data = canonical_path(ROOT)
    with data.open() as stream:
        rows = [json.loads(line) for line in stream if '"996fc37f49d9"' in line]
    return next(row["program_solution"] for row in rows if row.get("task_id") == "996fc37f49d9")


def test_exact_default_program_and_alternate_program_are_distinct():
    adapter = _load()
    assert adapter.program(SETTINGS[0]) == _canonical_program()
    assert adapter.program(SETTINGS[1]) != adapter.program(SETTINGS[0])


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_counts_labels_and_distinct_inputs(settings, demos, queries):
    adapter = _load()
    episode = adapter.generate(17, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == adapter.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    assert all(pair["output"] == adapter.solve(pair["input"], settings) for pair in pairs)


def test_inputs_are_setting_neutral_and_minimum_demos_identify_metric():
    adapter = _load()
    full_a = adapter.generate(29, SETTINGS[0], demos=6, queries=4)
    full_b = adapter.generate(29, SETTINGS[1], demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in full_a[split]] == [p["input"] for p in full_b[split]]
    assert any(a["output"] != b["output"] for a, b in zip(full_a["train"][:2], full_b["train"][:2]))
    assert adapter.generate(29, SETTINGS[0], demos=2, queries=4)["train"] == full_a["train"][:2]
    assert adapter.generate(29, SETTINGS[0], demos=6, queries=1)["test"] == full_a["test"][:1]


def test_fourth_query_is_substantive_30_by_30_stress():
    adapter = _load()
    grid = adapter.generate(5, SETTINGS[0], demos=2, queries=4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 45
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    assert len(adapter.components(grid)) == 3


def test_dependency_intermediate_metric_order_drives_repainting():
    adapter = _load()
    grid = adapter.generate(3, SETTINGS[0], demos=2, queries=1)["train"][0]["input"]
    cells = adapter.dependency_intermediate(grid, SETTINGS[0])
    boxes = adapter.dependency_intermediate(grid, SETTINGS[1])
    assert cells["ordered_components"] != boxes["ordered_components"]
    assert adapter.solve_from_intermediate(grid, cells) != adapter.solve_from_intermediate(grid, boxes)


@pytest.mark.parametrize("bad", [None, {}, {"rank_metric": "area"}, {"rank_metric": True}, {"rank_metric": "cells", "extra": 1}])
def test_invalid_settings_rejected(bad):
    adapter = _load()
    with pytest.raises(ValueError):
        adapter.program(bad)
    with pytest.raises(ValueError):
        adapter.generate(0, bad, demos=2, queries=1)


@pytest.mark.parametrize("name,bad", [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5)])
def test_invalid_controls_rejected(name, bad):
    adapter = _load()
    args = {"seed": 0, "settings": SETTINGS[0], "demos": 2, "queries": 1}
    args[name] = bad
    with pytest.raises(ValueError):
        adapter.generate(**args)


def test_deterministic_fresh_and_global_rng_isolated():
    adapter = _load()
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(41, SETTINGS[0], demos=2, queries=4)
    assert random.getstate() == before
    second = adapter.generate(41, SETTINGS[0], demos=2, queries=4)
    assert second == first
    first["train"][0]["input"][0][0] ^= 1
    assert adapter.generate(41, SETTINGS[0], demos=2, queries=4) == second


def _finite_rank_rivals(adapter, grid):
    groups = adapter.components(grid)

    def bbox(cells):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        return min(rows), min(cols), max(rows), max(cols)

    def box_area(cells):
        r0, c0, r1, c1 = bbox(cells)
        return (r1 - r0 + 1) * (c1 - c0 + 1)

    def perimeter(cells):
        occupied = set(cells)
        return sum(
            (row + dr, col + dc) not in occupied
            for row, col in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )

    def output(key, reverse=False):
        ordered = sorted(groups, key=lambda cells: (key(cells), cells), reverse=reverse)
        result = [[0 for _ in row] for row in grid]
        for rank, cells in enumerate(ordered):
            for row, col in cells:
                result[row][col] = (2, 3, 4)[rank]
        return result

    keys = {
        "density": lambda cells: len(cells) / box_area(cells),
        "scan_order": lambda cells: min(cells),
        "input_color": lambda cells: min(grid[row][col] for row, col in cells),
        "perimeter": perimeter,
        "bbox_perimeter": lambda cells: 2 * ((bbox(cells)[2] - bbox(cells)[0] + 1) + (bbox(cells)[3] - bbox(cells)[1] + 1)),
        "width": lambda cells: bbox(cells)[3] - bbox(cells)[1] + 1,
        "height": lambda cells: bbox(cells)[2] - bbox(cells)[0] + 1,
    }
    return {
        **{name: output(key) for name, key in keys.items()},
        **{name + "_descending": output(key, reverse=True) for name, key in keys.items()},
    }


@pytest.mark.parametrize("seed", [0, 17, 29, 41])
@pytest.mark.parametrize("settings", SETTINGS)
def test_two_demo_minimum_rejects_finite_rank_shortcuts(seed, settings):
    adapter = _load()
    episode = adapter.generate(seed, settings, demos=2, queries=4)
    for name in _finite_rank_rivals(adapter, episode["train"][0]["input"]):
        matches = [
            _finite_rank_rivals(adapter, pair["input"])[name] == pair["output"]
            for pair in episode["train"]
        ]
        assert not all(matches), (seed, settings, name)
