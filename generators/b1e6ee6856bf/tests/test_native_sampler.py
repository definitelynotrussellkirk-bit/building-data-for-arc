"""Input-bank contracts; executable rule/Racket checks live in adapter tests."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import random

import pytest


SAMPLER = Path(__file__).resolve().parents[1] / "workspace/parametric/sampler.py"


@lru_cache(None)
def sampler():
    assert SAMPLER.is_file(), "native input sampler has not been implemented"
    spec = importlib.util.spec_from_file_location("_b1e6ee_native_sampler_test", SAMPLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tops(grid):
    cells = []
    for col in range(len(grid[0])):
        occupied = [(row, col, grid[row][col]) for row in range(len(grid)) if grid[row][col]]
        if occupied:
            cells.append(occupied[0])
    return cells


def modes(counts):
    maximum = max(counts.values(), default=0)
    return {color for color, count in counts.items() if count == maximum}


def component_counts(cells):
    remaining = {(row, col): color for row, col, color in cells}
    counts = Counter()
    while remaining:
        start = next(iter(remaining))
        color = remaining.pop(start)
        counts[color] += 1
        pending = [start]
        while pending:
            row, col = pending.pop()
            for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if remaining.get(nxt) == color:
                    remaining.pop(nxt)
                    pending.append(nxt)
    return counts


@pytest.mark.parametrize("seed", [0, 42, 2**63 - 1])
def test_sampler_emits_only_distinct_lawful_inputs(seed):
    bank = sampler().sample_inputs(seed, demos=6, queries=4)
    assert set(bank) == {"train", "test"}
    assert len(bank["train"]) == 6 and len(bank["test"]) == 4
    grids = bank["train"] + bank["test"]
    assert len({json.dumps(grid) for grid in grids}) == 10
    for grid in grids:
        assert type(grid) is list and 1 <= len(grid) <= 30
        assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    rows = [row for grid in grids for row in grid]
    assert len({id(row) for row in rows}) == len(rows)


@pytest.mark.parametrize("seed", [0, 591, 2**63 - 1])
def test_independent_demo_query_counts_preserve_complete_bank_prefixes(seed):
    complete = sampler().sample_inputs(seed, demos=6, queries=4)
    for demos in (3, 4, 5, 6):
        for queries in (1, 2, 3, 4):
            requested = sampler().sample_inputs(seed, demos=demos, queries=queries)
            assert requested == {"train": complete["train"][:demos], "test": complete["test"][:queries]}
    assert sampler().sample_inputs(seed) == {"train": complete["train"][:3], "test": complete["test"]}


def test_reproducible_draws_do_not_touch_global_rng_or_share_mutable_grids():
    state = random.getstate()
    first = sampler().sample_inputs(815)
    assert random.getstate() == state
    second = sampler().sample_inputs(815)
    assert first == second
    first["train"][0][0][0] = (first["train"][0][0][0] + 1) % 10
    assert first != second
    assert sampler().sample_inputs(815) == second
    assert sampler().sample_inputs(816) != second


class IntSubclass(int):
    pass


@pytest.mark.parametrize("seed", [-1, 2**63, True, False, 1.0, "1", None, IntSubclass(1)])
def test_invalid_seed_types_and_bounds_are_rejected(seed):
    with pytest.raises((TypeError, ValueError)):
        sampler().sample_inputs(seed)


@pytest.mark.parametrize("argument,value", [
    ("demos", 2), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("demos", "3"), ("demos", None), ("demos", IntSubclass(3)),
    ("queries", 0), ("queries", 5), ("queries", True), ("queries", 1.0),
    ("queries", "1"), ("queries", None), ("queries", IntSubclass(1)),
])
def test_invalid_independent_counts_are_rejected(argument, value):
    with pytest.raises((TypeError, ValueError)):
        sampler().sample_inputs(0, **{argument: value})


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_first_demo_teaches_skyline_plurality_after_erasure(seed):
    grid = sampler().sample_inputs(seed)["train"][0]
    skyline = tops(grid)
    histogram = Counter(color for _, _, color in skyline)
    raw = Counter(color for row in grid for color in row if color)
    assert sorted(histogram.values()) == [1, 2, 3, 4]
    assert 2 * max(histogram.values()) < len(skyline)
    assert modes(raw).isdisjoint(modes(histogram))
    assert modes(component_counts(skyline)) != modes(histogram)
    assert len(skyline) < len(grid[0])  # Empty columns are meaningful.
    assert len({row for row, _, _ in skyline}) > 1
    assert max(sum(bool(row[col]) for row in grid) for col in range(len(grid[0]))) >= 3
    selected = modes(histogram)
    assert any(grid[row][col] in selected for top, col, _ in skyline
               for row in range(top + 1, len(grid)))  # Filtering all matching cells is wrong.
    assert any(sum(bool(row[col]) for row in grid) == 1 for _, col, _ in skyline)


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_second_demo_teaches_keep_all_tied_modes_and_drop_nonmodes(seed):
    grid = sampler().sample_inputs(seed)["train"][1]
    skyline = tops(grid)
    histogram = Counter(color for _, _, color in skyline)
    assert sorted(histogram.values()) == [1, 2, 3, 3]
    winners = modes(histogram)
    assert len(winners) == 2
    assert sum(color in winners for _, _, color in skyline) == 6
    assert any(color in winners and sum(bool(row[col]) for row in grid) == 1
               for _, col, color in skyline)
    assert any(color not in winners for _, _, color in skyline)


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_third_demo_preserves_canonical_scale_all_unique_top_tie(seed):
    grid = sampler().sample_inputs(seed)["train"][2]
    assert (len(grid), len(grid[0])) == (5, 5)
    assert {cell for row in grid for cell in row} == set(range(10))
    histogram = Counter(color for _, _, color in tops(grid))
    assert len(histogram) == 5 and set(histogram.values()) == {1}
    assert max(sum(bool(row[col]) for row in grid) for col in range(5)) == 3


@pytest.mark.parametrize("seed", [0, 93, 2**63 - 1])
def test_query_bank_reaches_substantive_edges_and_size_boundaries(seed):
    queries = sampler().sample_inputs(seed)["test"]
    by_shape = {(len(grid), len(grid[0])): grid for grid in queries}
    assert {(14, 18), (24, 26), (30, 30)} <= by_shape.keys()
    assert sum(height <= 3 and width <= 3 for height, width in by_shape) == 1
    for shape in ((14, 18), (24, 26), (30, 30)):
        grid = by_shape[shape]
        assert sum(bool(cell) for row in grid for cell in row) >= shape[0] * shape[1] // 3
        assert any(grid[0]) and any(grid[-1])
        assert any(row[0] for row in grid) and any(row[-1] for row in grid)
        assert len({row for row, _, _ in tops(grid)}) >= 3
        assert len(tops(grid)) >= len(grid[0]) - 3
        assert any(cell == 0 for row in grid for cell in row)


def test_query_presentation_order_is_not_fixed_to_source_size_order():
    orders = {tuple((len(g), len(g[0])) for g in sampler().sample_inputs(seed)["test"])
              for seed in range(12)}
    assert len(orders) >= 4
    assert len({order[0] for order in orders}) >= 3


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_thirty_by_thirty_query_requires_modal_filtering(seed):
    path = SAMPLER.with_name("native_family.py")
    spec = importlib.util.spec_from_file_location("_b1e6ee_sampler_stress_family", path)
    assert spec is not None and spec.loader is not None
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)
    grid = next(grid for grid in sampler().sample_inputs(seed)["test"]
                if (len(grid), len(grid[0])) == (30, 30))
    assert family.apply(grid, "all") != family.apply(grid, "modal_color")
    histogram = Counter(color for _, _, color in tops(grid))
    assert 3 <= len(histogram) <= 7
    assert min(histogram.values()) >= 3
