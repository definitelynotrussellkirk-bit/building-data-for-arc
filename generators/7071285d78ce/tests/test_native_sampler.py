"""Input-bank and teaching regressions for the opt-in transpose/rank family.

The independent competitors here diagnose geometry, not label authority.
Protected Racket execution is recorded by qualification and the bounded audit.
"""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"native {name} is not implemented"
    spec = importlib.util.spec_from_file_location(f"transpose_7071285d78ce_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sampler():
    return _load("sampler")


@pytest.fixture(scope="module")
def family():
    return _load("native_family")


def _key(grid):
    return tuple(map(tuple, grid))


def _parts(grid, *, diagonal=False, colorblind=False):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in steps:
                point = r + dr, c + dc
                if point in remaining and (colorblind or grid[point[0]][point[1]] == color):
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(cells)
    return result


def _paint(grid, groups):
    out = [[0] * len(grid[0]) for _ in grid]
    for cells in groups:
        for r, c in cells:
            out[r][c] = grid[r][c]
    return out


def _box_area(cells):
    return ((max(r for r, c in cells) - min(r for r, c in cells) + 1)
            * (max(c for r, c in cells) - min(c for r, c in cells) + 1))


def _select(grid, mode, *, diagonal=False, colorblind=False, bbox=False, one=False, whole_color=False):
    if mode == "all":
        return copy.deepcopy(grid)
    parts = _parts(grid, diagonal=diagonal, colorblind=colorblind)
    if whole_color:
        colors = sorted({grid[r][c] for cells in parts for r, c in cells})
        parts = [{(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
                 for color in colors]
    metric = _box_area if bbox else len
    best = (max if mode == "largest" else min)(map(metric, parts))
    selected = [part for part in parts if metric(part) == best]
    return _paint(grid, selected[:1] if one else selected)


def _local(grid, transform="transpose"):
    out = [[0] * len(grid[0]) for _ in grid]
    for cells in _parts(grid):
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        height = max(r for r, c in cells) - r0 + 1
        width = max(c for r, c in cells) - c0 + 1
        for r, c in cells:
            a, b = r - r0, c - c0
            aa, bb = {
                "transpose": (b, a), "cw": (b, height - 1 - a),
                "ccw": (width - 1 - b, a), "half": (height - 1 - a, width - 1 - b),
                "lr": (a, width - 1 - b), "ud": (height - 1 - a, b),
                "anti": (width - 1 - b, height - 1 - a),
                "nonsquare_only": (b, a) if height != width else (a, b),
                "source_size_at_most_five": (b, a) if len(cells) <= 5 else (a, b),
            }[transform]
            rr, cc = r0 + aa, c0 + bb
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                out[rr][cc] = grid[r][c]
    return out


def _competitors(grid, mode):
    intermediate = _local(grid)
    rivals = {
        "skip_transpose": _select(grid, mode),
        "select_before_transpose": _local(_select(grid, mode)),
        "eight_connected_postselection": _select(intermediate, mode, diagonal=True),
        "colorblind_four_postselection": _select(intermediate, mode, colorblind=True),
        "bbox_area_postselection": _select(intermediate, mode, bbox=True),
        "one_extremum_only": _select(intermediate, mode, one=True),
        "whole_color_postselection": _select(intermediate, mode, whole_color=True),
        "transpose_nonsquare_only": _select(_local(grid, "nonsquare_only"), mode),
        "transpose_source_size_at_most_five": _select(_local(grid, "source_size_at_most_five"), mode),
    }
    rivals.update({f"local_{name}": _select(_local(grid, name), mode)
                   for name in ("cw", "ccw", "half", "lr", "ud", "anti")})
    for size in (1, 2, 3, 4, 5, 6, 8, 10):
        rivals[f"fixed_area_{size}"] = _paint(intermediate, [part for part in _parts(intermediate) if len(part) == size])
    for color in range(1, 10):
        rivals[f"fixed_color_{color}"] = [[value if value == color else 0 for value in row] for row in intermediate]
    return rivals


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_full_bank_contains_ten_unique_lawful_independent_grids(sampler, family, seed):
    # Dropping a component, colliding destinations, or cloning a query fails.
    episode = sampler.inputs(seed, demos=6, queries=4)
    assert set(episode) == {"train", "test"}
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    grids = episode["train"] + episode["test"]
    assert len({_key(grid) for grid in grids}) == 10
    assert len({id(row) for grid in grids for row in grid}) == sum(map(len, grids))
    for grid in grids:
        info = family.validate_grid(grid)
        assert 2 <= len(info["components"]) <= 24
        assert type(grid) is list and all(type(row) is list for row in grid)
        assert all(type(value) is int for row in grid for value in row)
        transformed = _local(grid)
        assert sum(value != 0 for row in grid for value in row) == sum(value != 0 for row in transformed for value in row)


@pytest.mark.parametrize("demos,queries", [(3, 1), (3, 4), (4, 2), (5, 3), (6, 1)])
def test_counts_only_slice_independent_banks(sampler, demos, queries):
    complete = sampler.inputs(481, demos=6, queries=4)
    partial = sampler.inputs(481, demos=demos, queries=queries)
    assert partial["train"] == complete["train"][:demos]
    assert partial["test"] == complete["test"][:queries]
    assert sampler.inputs(481) == {"train": complete["train"][:3], "test": complete["test"]}


def test_sampler_is_fresh_deterministic_and_does_not_touch_global_rng(sampler):
    random.seed(10451)
    state = random.getstate()
    first = sampler.inputs(90210, demos=6, queries=4)
    assert random.getstate() == state
    expected = copy.deepcopy(first)
    second = sampler.inputs(90210, demos=6, queries=4)
    assert first == second and first is not second
    assert all(a is not b for split in ("train", "test") for a, b in zip(first[split], second[split]))
    first["train"][0][0][0] = 8
    first["test"].pop()
    assert sampler.inputs(90210, demos=6, queries=4) == expected
    assert random.getstate() == state
    assert sampler.inputs(90211, demos=6, queries=4) != expected


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 1.0, "1", None])
def test_seed_requires_bounded_exact_integer(sampler, seed):
    with pytest.raises(ValueError):
        sampler.inputs(seed)


@pytest.mark.parametrize("demos", [True, False, 2, 7, 3.0, "3", None])
def test_demo_count_requires_exact_integer_three_through_six(sampler, demos):
    with pytest.raises(ValueError):
        sampler.inputs(0, demos=demos)


@pytest.mark.parametrize("queries", [True, False, 0, 5, 1.0, "1", None])
def test_query_count_requires_exact_integer_one_through_four(sampler, queries):
    with pytest.raises(ValueError):
        sampler.inputs(0, queries=queries)


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_first_three_demos_construct_mergers_ranking_ties_and_simple_shapes(sampler, seed):
    demos = sampler.inputs(seed)["train"]
    ranked = [_parts(_local(grid)) for grid in demos]
    assert [sorted(map(len, parts)) for parts in ranked] == [[4, 4, 5], [6, 6, 8, 8], [1, 1, 2, 3, 5, 10]]
    assert all(len(_parts(_local(grid))) < len(_parts(grid)) for grid in demos)
    for mode in ("largest", "smallest"):
        assert any(_select(_local(grid), mode) != _local(_select(grid, mode)) for grid in demos)
        assert any(sum(len(part) == (max if mode == "largest" else min)(map(len, parts)) for part in parts) > 1
                   for parts in ranked)
    assert any(len(part) == 1 for grid in demos for part in _parts(grid))
    assert any(len(part) > 1 and _box_area(part) == len(part) for grid in demos for part in _parts(grid))
    assert any((max(r for r, c in part) - min(r for r, c in part)
                != max(c for r, c in part) - min(c for r, c in part)) and _box_area(part) > len(part)
               for grid in demos for part in _parts(grid))


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
@pytest.mark.parametrize("mode", ["all", "largest", "smallest"])
def test_no_declared_rival_fits_three_demos_then_changes_a_query(sampler, family, seed, mode):
    # Removing a distinguishing demonstration exposes an unsupported query.
    episode = sampler.inputs(seed)
    grids = episode["train"] + episode["test"]
    labels = [family.apply(grid, {"selection": mode}) for grid in grids]
    predicted = [_competitors(grid, mode) for grid in grids]
    names = predicted[0]
    for name in names:
        if all(row[name] == label for row, label in zip(predicted[:3], labels[:3])):
            assert all(row[name] == label for row, label in zip(predicted[3:], labels[3:])), name


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_three_demos_separate_connectivity_color_bbox_and_tie_rivals(sampler, seed):
    demos = sampler.inputs(seed)["train"]
    for mode in ("largest", "smallest"):
        for rival in ("eight_connected_postselection", "colorblind_four_postselection",
                      "bbox_area_postselection", "one_extremum_only", "whole_color_postselection"):
            assert any(_competitors(grid, mode)[rival] != _select(_local(grid), mode) for grid in demos), (mode, rival)
    # Source/destination overlap is lawful and requires a fresh output canvas.
    assert any(any(target & other for j, other in enumerate(_parts(grid)) if j != index)
               for grid in demos
               for index, cells in enumerate(_parts(grid))
               for target in [{(min(r for r, c in cells) + c - min(c for r, c in cells),
                                min(c for r, c in cells) + r - min(r for r, c in cells)) for r, c in cells}])


@pytest.mark.parametrize("seed", [0, 17, 19, 20261025, 2**63 - 1])
@pytest.mark.parametrize("rival", ["transpose_nonsquare_only", "transpose_source_size_at_most_five"])
def test_smallest_minimum_lesson_teaches_square_and_large_selected_components(sampler, seed, rival):
    # A six-cell 3x3 query must not be the first selected square or >5-cell
    # source. Earlier smallest lessons discarded every such transformed piece.
    demos = sampler.inputs(seed, demos=3)["train"]
    assert any(_competitors(grid, "smallest")[rival] != _select(_local(grid), "smallest")
               for grid in demos), rival


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_queries_cover_minimum_rectangles_and_dense_thirty_with_boundary_contacts(sampler, family, seed):
    queries = sampler.inputs(seed)["test"]
    assert {tuple(sorted((len(grid), len(grid[0])))) for grid in queries} == {(8, 8), (20, 24), (24, 26), (30, 30)}
    large = next(grid for grid in queries if len(grid) == len(grid[0]) == 30)
    info = family.validate_grid(large)
    assert len(info["components"]) == 24
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 100
    assert min(r for r, c in occupied) == min(c for r, c in occupied) == 0
    assert max(r for r, c in occupied) == max(c for r, c in occupied) == 29
    assert len(_parts(large)) - len(_parts(_local(large))) >= 8
    assert len({len(part) for part in _parts(_local(large))}) > 1


def test_seeds_vary_query_order_palette_and_large_shape_topology(sampler):
    episodes = [sampler.inputs(seed) for seed in (0, 19, 20261025, 2**63 - 1)]
    assert len({tuple((len(grid), len(grid[0])) for grid in episode["test"]) for episode in episodes}) > 1
    assert len({tuple(sorted({value for grid in episode["train"] for row in grid for value in row if value}))
                for episode in episodes}) > 1
    normalized = []
    for episode in episodes:
        large = next(grid for grid in episode["test"] if len(grid) == len(grid[0]) == 30)
        normalized.append(tuple(tuple(int(value != 0) for value in row) for row in large))
    assert len(set(normalized)) > 1
