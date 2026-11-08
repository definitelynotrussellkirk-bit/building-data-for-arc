"""Constructive curriculum and prefix contracts for the native input sampler."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest


SAMPLER = Path(__file__).resolve().parents[1] / "workspace/parametric/sampler.py"


def _load():
    assert SAMPLER.is_file(), "native sampler must provide the constructive input bank"
    spec = importlib.util.spec_from_file_location("native_sampler_11c53dabb028", SAMPLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid, *, diagonal=False, monochrome=False):
    """Test-local flood fill, independent of the family implementation."""
    pending = {(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value != 0}
    components = []
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    while pending:
        first = min(pending)
        pending.remove(first)
        cells = {first}
        frontier = [first]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in steps:
                point = r + dr, c + dc
                if point not in pending:
                    continue
                if monochrome and grid[point[0]][point[1]] != grid[r][c]:
                    continue
                pending.remove(point)
                cells.add(point)
                frontier.append(point)
        components.append(sorted(cells))
    return components


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _area(cells):
    top, left, bottom, right = _bbox(cells)
    return (bottom - top + 1) * (right - left + 1)


def _winner(grid, **kwargs):
    return min(_components(grid, **kwargs), key=lambda cells: (-len(cells), cells[0]))


def _crop(grid, cells):
    top, left, bottom, right = _bbox(cells)
    keep = set(cells)
    return [[grid[r][c] if (r, c) in keep else 0
             for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]


def _frames(grid):
    return grid, _crop(grid, _winner(grid))


def _first(grid):
    return next((r, c, value) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value)


def test_counts_exact_types_and_domain_bounds():
    sampler = _load()
    for seed in (0, 17, 2**63 - 1):
        episode = sampler.sample_inputs(seed, demos=6, queries=4)
        assert set(episode) == {"train", "test"}
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 4
        grids = episode["train"] + episode["test"]
        assert len({repr(grid) for grid in grids}) == 10
        for grid in grids:
            assert type(grid) is list and 1 <= len(grid) <= 15
            assert type(grid[0]) is list and 1 <= len(grid[0]) <= 15
            assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
            values = [value for row in grid for value in row]
            assert all(type(value) is int and 0 <= value <= 9 for value in values)
            assert 0 in values and any(values)
    for name, values in {
        "seed": (True, 1.0, "1", -1, 2**63),
        "demos": (True, 3.0, 2, 7),
        "queries": (True, 1.0, 0, 5),
    }.items():
        for value in values:
            args = {"seed": 0, "demos": 3, "queries": 4, name: value}
            with pytest.raises((TypeError, ValueError)):
                sampler.sample_inputs(**args)


def test_complete_banks_have_independent_stable_prefixes_and_fresh_lists():
    sampler = _load()
    state = random.getstate()
    for seed in (0, 17, 2**63 - 1):
        full = sampler.sample_inputs(seed, 6, 4)
        frozen = deepcopy(full)
        for demos, queries in ((3, 1), (3, 4), (4, 2), (5, 3), (6, 1)):
            small = sampler.sample_inputs(seed, demos, queries)
            assert small["train"] == full["train"][:demos]
            assert small["test"] == full["test"][:queries]
        full["train"][0][0][0] = 99
        full["test"][0][0][0] = 99
        assert sampler.sample_inputs(seed, 6, 4) == frozen
    assert random.getstate() == state
    first_shapes = {
        (len(sample["test"][0]), len(sample["test"][0][0]))
        for sample in (sampler.sample_inputs(seed, 3, 1) for seed in range(12))
    }
    assert len(first_shapes) > 1, "the complete query bank must be shuffled before slicing"


def test_three_demos_separate_component_size_ties_connectivity_and_isolation():
    sampler = _load()
    for seed in (0, 1, 17, 921):
        first, tied, anchor = sampler.sample_inputs(seed)["train"]
        pieces = _components(first)
        chosen = _winner(first)
        assert chosen != pieces[0] and chosen != pieces[-1]
        assert all(len(chosen) > len(piece) for piece in pieces if piece != chosen)
        assert any(_area(piece) > _area(chosen) for piece in pieces)
        assert chosen != _winner(first, diagonal=True)
        assert chosen != _winner(first, monochrome=True)
        top, left, bottom, right = _bbox(chosen)
        assert any(first[r][c] and (r, c) not in chosen
                   for r in range(top, bottom + 1) for c in range(left, right + 1))
        assert len({first[r][c] for r, c in chosen}) >= 3

        pieces = _components(tied)
        maximum = max(map(len, pieces))
        ties = [piece for piece in pieces if len(piece) == maximum]
        chosen = _winner(tied)
        assert len(ties) >= 2
        assert chosen == min(ties, key=lambda cells: cells[0])
        assert chosen != max(ties, key=lambda cells: cells[0])
        assert chosen != min(ties, key=lambda cells: min(c for _, c in cells))
        assert chosen != min(ties, key=lambda cells: _bbox(cells)[:2])
        assert all(_crop(tied, chosen) != _crop(tied, rival)
                   for rival in ties if rival != chosen)

        assert len(_components(anchor)) == 1
        assert _bbox(_winner(anchor)) == (0, 0, len(anchor) - 1, len(anchor[0]) - 1)
        assert len(anchor) <= 5 and len(anchor[0]) <= 5
        for grid in (first, tied, anchor):
            assert any(value == 0 for row in _frames(grid)[1] for value in row)


def test_first_color_roles_refute_frequency_extremes_and_both_scan_shortcuts():
    sampler = _load()
    for seed in (0, 1, 17, 921):
        demos = sampler.sample_inputs(seed)["train"]
        assert _first(demos[0])[2] != _first(_frames(demos[0])[1])[2]
        for frame_index in (0, 1):
            frames = [_frames(grid)[frame_index] for grid in demos]
            profiles = []
            for grid in frames:
                color = _first(grid)[2]
                counts = Counter(value for row in grid for value in row if value)
                profiles.append((color, counts))
            assert any(min(counts) < color < max(counts)
                       and counts[color] < max(counts.values())
                       for color, counts in profiles)
            assert any(color == min(counts) and 2 * counts[color] > sum(counts.values())
                       for color, counts in profiles)
            assert any(color == max(counts) and 2 * counts[color] > sum(counts.values())
                       for color, counts in profiles)
            assert any(
                _first(grid)[1] == 0
                and any(value not in (0, _first(grid)[2])
                        for value in grid[_first(grid)[0]][1:])
                for grid in frames
            ), "columns 1..w-1 then 0 must fail on a visible demo"
            assert any(
                _first(grid)[1] > 0
                and next(grid[r][c] for c in range(len(grid[0]))
                         for r in range(len(grid)) if grid[r][c]) != _first(grid)[2]
                for grid in frames
            ), "column-major color selection must fail on a visible demo"


def test_queries_cover_solid_derived_frame_and_substantive_full_size_isolation():
    sampler = _load()
    for seed in (0, 1, 17, 921):
        tests = sampler.sample_inputs(seed)["test"]
        by_shape = {(len(grid), len(grid[0])): grid for grid in tests}
        assert set(by_shape) == {(1, 2), (9, 13), (13, 11), (15, 15)}
        tiny = by_shape[(1, 2)]
        assert len(_winner(tiny)) == 1
        assert _frames(tiny)[1] == [[next(value for value in tiny[0] if value)]]
        large = by_shape[(15, 15)]
        selected = _winner(large)
        assert _bbox(selected) == (0, 0, 14, 14)
        assert len(selected) >= 75
        assert sum(value == 0 for row in large for value in row) >= 25
        assert len({large[r][c] for r, c in selected}) >= 3
        frame = _frames(large)[1]
        assert (len(frame), len(frame[0])) == (15, 15)
        assert frame != large
        assert any(large[r][c] and frame[r][c] == 0
                   for r in range(1, 14) for c in range(1, 14))
        assert all(any(value for value in edge)
                   for edge in (frame[0], frame[-1],
                                [row[0] for row in frame], [row[-1] for row in frame]))
