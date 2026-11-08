"""Native promotion regressions for the median/second-largest blob family."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "9c69eb63c11a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "native parametric adapter has not been built"
    name = "_test_9c69eb63c11a_parametric"
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending = deque([start])
        cells = []
        while pending:
            r, c = pending.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    pending.append(point)
        result.append(frozenset(cells))
    return sorted(result, key=len)


def _paint(grid, cells):
    return [
        [grid[r][c] if (r, c) in cells else 0 for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def _visible_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _serialized(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_default_program_is_exact_canonical_and_alternative_is_one_safe_rank_change():
    adapter = _load_adapter()
    median = adapter.program({"selection_mode": "median"})
    second = adapter.program({"selection_mode": "second_largest"})
    assert median == _canonical_program()
    assert second != median
    assert median.count("(quotient (length ranked) 2)") == 1
    assert second.count("(- (length ranked) 2)") == 1
    assert "(quotient (length ranked) 2)" not in second


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"selection_mode": "median", "extra": 1},
     {"selection_mode": True}, {"selection_mode": 0},
     {"selection_mode": "largest"}],
)
def test_settings_validation_rejects_undeclared_or_coerced_values(settings):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 2, 4), (-1, 2, 4), (1.5, 2, 4),
        (0, True, 4), (0, 1, 4), (0, 7, 4),
        (0, 2, True), (0, 2, 3), (0, 2, 5),
    ],
)
def test_generate_rejects_invalid_seed_or_count_boundaries(seed, demos, queries):
    adapter = _load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"selection_mode": "median"}, demos, queries)


@pytest.mark.parametrize("demos", [2, 6])
def test_min_and_max_demo_counts_produce_exact_private_contract(demos):
    adapter = _load_adapter()
    episode = adapter.generate(20261025, {"selection_mode": "second_largest"}, demos, 4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"selection_mode": "second_largest"})
    assert all(set(pair) == {"input", "output"} for split in ("train", "test") for pair in episode[split])
    inputs = [_serialized(grid) for grid in _visible_inputs(episode)]
    assert len(inputs) == len(set(inputs))


def test_inputs_are_deterministic_and_identical_across_modes_and_each_demo_separates_them():
    adapter = _load_adapter()
    median = adapter.generate(44617, {"selection_mode": "median"}, 2, 4)
    second = adapter.generate(44617, {"selection_mode": "second_largest"}, 2, 4)
    assert _visible_inputs(median) == _visible_inputs(second)
    assert adapter.generate(44617, {"selection_mode": "median"}, 2, 4) == median
    for left, right in zip(median["train"], second["train"]):
        assert left["output"] != right["output"]


def test_every_pair_selects_the_declared_rank_and_refutes_fixed_extreme_rivals():
    adapter = _load_adapter()
    for mode, rank in (("median", 2), ("second_largest", 3)):
        episode = adapter.generate(7001, {"selection_mode": mode}, 3, 4)
        for pair in [*episode["train"], *episode["test"]]:
            ranked = _components(pair["input"])
            assert len(ranked) == 5
            assert len({len(cells) for cells in ranked}) == 5
            assert pair["output"] == _paint(pair["input"], ranked[rank])
            assert pair["output"] != _paint(pair["input"], ranked[0])
            assert pair["output"] != _paint(pair["input"], ranked[-1])
            if mode == "median":
                assert pair["output"] != _paint(pair["input"], ranked[-2])


def test_query_bank_contains_small_boundary_and_dense_30x30_rank_stress():
    adapter = _load_adapter()
    episode = adapter.generate(99, {"selection_mode": "median"}, 3, 4)
    query_inputs = [pair["input"] for pair in episode["test"]]
    shapes = {(len(grid), len(grid[0])) for grid in query_inputs}
    assert (8, 8) in shapes
    assert (30, 30) in shapes
    stress = next(grid for grid in query_inputs if (len(grid), len(grid[0])) == (30, 30))
    sizes = [len(cells) for cells in _components(stress)]
    assert sizes == [17, 31, 47, 63, 79]
    assert sum(value != 0 for row in stress for value in row) == 237
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 20
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 20
