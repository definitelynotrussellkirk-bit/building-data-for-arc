"""Focused contracts for the separate native input sampler.

These tests check the sampled inputs and their teaching geometry. Protected
Racket label execution is recorded separately by native qualification/audit.
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
    spec = importlib.util.spec_from_file_location(f"orbit_7fe59337a0b4_{name}", path)
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


def _sector(info):
    r0, c0, r1, c1 = info["bbox"]
    mr, mc = info["marker"]
    vertical = "N" if r1 < mr else "S" if r0 > mr else ""
    horizontal = "W" if c1 < mc else "E" if c0 > mc else ""
    return vertical + horizontal


def _axis_words(grid, marker):
    mr, mc = marker
    words = []
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        word = []
        row, col = mr + dr, mc + dc
        while 0 <= row < len(grid) and 0 <= col < len(grid):
            word.append(grid[row][col] != 0)
            row, col = row + dr, col + dc
        words.append(word)
    return words


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_full_bank_has_ten_unique_lawful_connected_inputs(sampler, family, seed):
    # Broken grammar, duplicate sampling, or a truncated full bank fails here.
    episode = sampler.inputs(seed, demos=6, queries=4)
    assert set(episode) == {"train", "test"}
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 4
    grids = episode["train"] + episode["test"]
    assert len({_key(grid) for grid in grids}) == 10
    assert len({id(row) for grid in grids for row in grid}) == sum(map(len, grids))
    for grid in grids:
        info = family.validate_grid(grid)
        assert type(grid) is list and all(type(row) is list for row in grid)
        assert all(type(value) is int for row in grid for value in row)
        assert len({point for part in info["placements"] for point in part}) == 4 * len(info["motif_cells"])
        assert all(any(word) for word in _axis_words(family.orbit(grid), info["marker"]))


@pytest.mark.parametrize("demos, queries", [(3, 1), (3, 4), (4, 2), (5, 3), (6, 1)])
def test_counts_only_slice_independent_complete_banks(sampler, demos, queries):
    # Sharing an RNG across count-dependent loops would alter one of these prefixes.
    complete = sampler.inputs(481, demos=6, queries=4)
    partial = sampler.inputs(481, demos=demos, queries=queries)
    assert partial["train"] == complete["train"][:demos]
    assert partial["test"] == complete["test"][:queries]
    assert sampler.inputs(481) == {"train": complete["train"][:3], "test": complete["test"]}


def test_calls_are_deterministic_fresh_and_leave_global_rng_untouched(sampler):
    random.seed(10451)
    state = random.getstate()
    first = sampler.inputs(90210, demos=6, queries=4)
    assert random.getstate() == state
    expected = copy.deepcopy(first)
    second = sampler.inputs(90210, demos=6, queries=4)
    assert first == second
    assert first is not second and first["train"] is not second["train"]
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
def test_three_demos_constructively_cover_source_and_first_hit_distinctions(sampler, family, seed):
    # Losing a witness permits cardinal-only/diagonal-only, fixed-gap, or
    # continue-through-hole shortcuts to survive a minimum-size lesson.
    grids = sampler.inputs(seed)["train"]
    infos = [family.validate_grid(grid) for grid in grids]
    assert _sector(infos[0]) == "N"
    assert _sector(infos[1]) in {"NW", "NE", "SW", "SE"}
    assert _sector(infos[2]) in {"E", "S", "W"}
    assert len({info["motif_color"] for info in infos}) == 3
    assert len(grids[0]) == 9
    r0, c0, _, _ = infos[0]["bbox"]
    assert {(r - r0, c - c0) for r, c in infos[0]["motif_cells"]} == {(0, 0), (0, 1), (1, 1)}
    assert infos[0]["motif_cells"] - set(infos[0]["placements"][0])

    words = [_axis_words(family.orbit(grid), info["marker"]) for grid, info in zip(grids, infos)]
    all_run_lengths = {word.index(True) for example in words for word in example}
    assert 1 in all_run_lengths and max(all_run_lengths) >= 3
    assert all(word.index(True) >= 3 for word in words[1])
    assert all(any(not word[i] and any(word[i + 1:]) for i in range(word.index(True) + 1, len(word))) for word in words[1])
    assert len(infos[2]["shape"][0]) % 2 == 0
    assert len(infos[2]["shape"]) != len(infos[2]["shape"][0])
    assert len({word.index(True) for word in words[2]}) > 1


@pytest.mark.parametrize("seed", [0, 19, 20261025, 2**63 - 1])
def test_queries_grow_real_content_to_thirty_with_edge_contact(sampler, family, seed):
    # Empty padding or cloning a small motif on the largest canvas fails here.
    episode = sampler.inputs(seed, demos=6, queries=4)
    by_size = {len(grid): grid for grid in episode["test"]}
    assert set(by_size) == {13, 21, 26, 30}
    minimum_heights = {13: 4, 21: 7, 26: 10, 30: 12}
    for size, grid in by_size.items():
        info = family.validate_grid(grid)
        assert len(info["shape"]) >= minimum_heights[size]
        points = {point for placement in info["placements"] for point in placement}
        assert max(r for r, c in points) - min(r for r, c in points) + 1 >= 2 * minimum_heights[size] + 3
        assert max(c for r, c in points) - min(c for r, c in points) + 1 >= 2 * minimum_heights[size] + 3
    large = family.validate_grid(by_size[30])
    assert (len(large["shape"]), len(large["shape"][0])) == (12, 3)
    assert len(large["motif_cells"]) >= 22
    assert len(large["motif_cells"]) < 36
    large_points = {point for placement in large["placements"] for point in placement}
    assert any(row in (0, 29) or col in (0, 29) for row, col in large_points)
    assert any(row in (0, 29) or col in (0, 29) for row, col in large["motif_cells"])


def test_seeds_vary_query_order_palette_and_large_motif_topology(sampler, family):
    episodes = [sampler.inputs(seed) for seed in (0, 19, 20261025, 2**63 - 1)]
    assert len({tuple(map(len, episode["test"])) for episode in episodes}) > 1
    assert len({tuple(family.validate_grid(grid)["motif_color"] for grid in episode["train"]) for episode in episodes}) > 1
    large_shapes = [family.validate_grid(next(grid for grid in episode["test"] if len(grid) == 30))["shape"] for episode in episodes]
    assert len({_key(shape) for shape in large_shapes}) > 1


def test_mandatory_l_demo_teaches_marker_instead_of_canvas_center(sampler, family):
    # A center-only core lesson leaves the later boundary marker under-taught.
    for seed in (0, 19, 20261025, 2**63 - 1):
        grid = sampler.inputs(seed)["train"][0]
        mr, mc = family.validate_grid(grid)["marker"]
        center = len(grid) // 2
        assert abs(mr - center) + abs(mc - center) >= 2
