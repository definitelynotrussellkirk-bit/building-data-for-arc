"""Public-contract regressions for the endpoint-seeded induced path domain.

The graph checks below are independent of the generator's validator and path
constructor.  The joint-axis test covers all 4,590 band/height/width/length
combinations, using one deterministic draw each; this is finite coverage, not
an all-seed claim.  Both library and copied-runtime layouts are supported.
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
from pathlib import Path
import sys

import pytest


TASK_ID = "547c45a21db1"
BANDS = ("easy", "medium", "hard")

# Locate the public helper in this test's own tree, without relying on cwd or
# importing private scripts.  find_root then identifies the canonical-data root.
for _ancestor in Path(__file__).resolve().parents:
    _support = next(
        (candidate for candidate in (_ancestor, _ancestor / "shared" / "runtime")
         if (candidate / "reviewer_support.py").is_file()),
        None,
    )
    if _support is not None:
        sys.path.insert(0, str(_support))
        break
else:
    raise RuntimeError("No local reviewer_support.py found")

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file()
)
_spec = importlib.util.spec_from_file_location("path_contract_generator", GENERATOR_PATH)
assert _spec is not None and _spec.loader is not None
GEN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def assert_induced_endpoint_path(grid):
    """Check the declared domain from pixels and graph adjacency alone."""
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and row for row in grid)
    assert len({len(row) for row in grid}) == 1
    assert all(type(value) is int and value in (0, 1, 2, 3)
               for row in grid for value in row)
    active = {(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value != 0}
    seed2 = {(r, c) for r, c in active if grid[r][c] == 2}
    seed3 = {(r, c) for r, c in active if grid[r][c] == 3}
    assert len(seed2) == len(seed3) == 1
    assert sum(value == 1 for row in grid for value in row) >= 2
    neighbors = {
        (r, c): {(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        & active
        for r, c in active
    }
    endpoints = {cell for cell, adjacent in neighbors.items() if len(adjacent) == 1}
    assert endpoints == seed2 | seed3
    assert all(len(adjacent) in (1, 2) for adjacent in neighbors.values())
    reached = set()
    pending = list(seed2)
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(neighbors[current] - reached)
    assert reached == active
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "path_len": len(active)}


def strict_accepts(grid):
    verdict = GEN.strict_canonical_like(grid)
    assert type(verdict) is bool or isinstance(verdict, list)
    if isinstance(verdict, list):
        assert all(isinstance(item, str) for item in verdict)
        return not verdict
    return verdict


VALID_MINIMUM = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 2, 1, 1, 3, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]

# Literal counterexamples avoid using a generator helper to define invalidity.
INVALID_GRIDS = [
    pytest.param([
        [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
        [2, 1, 1, 3, 0, 0], [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1],
    ], id="disconnected-extra-component"),
    pytest.param([
        [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
        [2, 1, 0, 1, 3, 0], [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ], id="seeds-in-separate-components"),
    pytest.param([
        [0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0],
        [2, 1, 1, 1, 3, 0], [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ], id="branch"),
    pytest.param([
        [2, 1, 1, 0, 0, 0], [1, 0, 1, 0, 0, 0],
        [1, 1, 3, 0, 0, 0], [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ], id="cycle"),
    pytest.param([
        [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
        [1, 2, 1, 3, 1, 0], [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ], id="seeds-not-at-endpoints"),
    pytest.param([[2, 1, 2, 1, 3]], id="duplicate-seed"),
    pytest.param([[2, 1, 1, 1, 1]], id="missing-seed"),
    pytest.param([[2, 1, 3]], id="too-few-ones"),
    pytest.param([[2, 1, 1, 3, 4]], id="foreign-color"),
    pytest.param([[2, 1, 1, 3, -1]], id="negative-color"),
    pytest.param([[2, True, 1, 3]], id="boolean-path-cell"),
    pytest.param([[2, 1, 1, 3, False]], id="boolean-background"),
    pytest.param([[2, 1.0, 1, 3]], id="float-path-cell"),
    pytest.param([[2, 1, 1, 3, 0.0]], id="float-background"),
    pytest.param([[2, 1, 1, 3, "0"]], id="string-cell"),
    pytest.param([[2, 1, 1, 3], [0]], id="ragged"),
    pytest.param([(2, 1, 1, 3)], id="tuple-row"),
    pytest.param([[2, 1, 1, 3], None], id="missing-row"),
    pytest.param([], id="empty-grid"),
    pytest.param([[]], id="empty-row"),
    pytest.param(None, id="missing-grid"),
    pytest.param(7, id="scalar-grid"),
]


def test_two_color_one_cells_are_sufficient():
    assert_induced_endpoint_path(VALID_MINIMUM)
    assert GEN.self_check(copy.deepcopy(VALID_MINIMUM)) == []


def test_all_three_canonical_pairs_are_supported():
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        grid = copy.deepcopy(pair["input"])
        assert_induced_endpoint_path(grid)
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("grid", INVALID_GRIDS)
def test_self_check_rejects_malformed_or_nonpath_grids(grid):
    original = copy.deepcopy(grid)
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)
    assert grid == original


@pytest.mark.parametrize("grid", INVALID_GRIDS)
def test_strict_validator_rejects_malformed_or_nonpath_grids(grid):
    assert not strict_accepts(copy.deepcopy(grid))


def test_strict_validator_accepts_all_canonical_inputs():
    for pair in CANONICAL:
        assert strict_accepts(copy.deepcopy(pair["input"]))


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("height", range(5, 15))
def test_every_joint_axis_combination_is_exact(difficulty, height):
    # Exhaust all widths and lengths at every height in every band.  In
    # particular, 5x6/length20 must succeed without clipping or shortening.
    for width, length in itertools.product(range(6, 15), range(4, 21)):
        overrides = {"grid_h": height, "grid_w": width, "path_len": length}
        sample_index = (height - 5) * 153 + (width - 6) * 17 + (length - 4)
        grid = GEN.generate(314159, sample_index, difficulty=difficulty, **overrides)
        assert assert_induced_endpoint_path(grid) == overrides
        assert GEN.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_draws_are_valid_and_deterministic(difficulty):
    for seed, sample_index in itertools.product((0, 1, 17, 314159), range(12)):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        observed = assert_induced_endpoint_path(grid)
        assert 5 <= observed["grid_h"] <= 14
        assert 6 <= observed["grid_w"] <= 14
        assert 4 <= observed["path_len"] <= 20
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.generate(seed, sample_index, difficulty=difficulty) == grid


@pytest.mark.parametrize("difficulty,shape", (
    ("easy", (5, 6, 6)), ("medium", (6, 7, 9)), ("hard", (9, 9, 14)),
))
def test_length_is_not_clipped_even_within_original_band_ranges(difficulty, shape):
    # These requests already fit the original advertised per-band bounds;
    # failures here expose shortening independently of the expanded domain.
    overrides = dict(zip(("grid_h", "grid_w", "path_len"), shape))
    for seed, sample_index in itertools.product((0, 1, 17), range(20)):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
        assert assert_induced_endpoint_path(grid) == overrides


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("shape", ((5, 6, 4), (5, 6, 20), (8, 9, 19), (14, 14, 20)))
def test_forced_extreme_and_canonical_length_draws_are_deterministic(difficulty, shape):
    overrides = dict(zip(("grid_h", "grid_w", "path_len"), shape))
    for seed, sample_index in itertools.product((0, 1, 17), range(8)):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
        assert assert_induced_endpoint_path(grid) == overrides
        assert GEN.generate(seed, sample_index, difficulty=difficulty, **overrides) == grid


@pytest.mark.parametrize("difficulty", BANDS)
def test_none_axis_overrides_have_default_behavior(difficulty):
    for sample_index in range(12):
        grid = GEN.generate(2718, sample_index, difficulty=difficulty)
        assert GEN.generate(2718, sample_index, difficulty=difficulty,
                            grid_h=None, grid_w=None, path_len=None) == grid


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 4), ("grid_h", 15),
    ("grid_w", 5), ("grid_w", 15),
    ("path_len", 3), ("path_len", 21),
    ("grid_h", "6"), ("grid_h", 6.0), ("grid_h", 6.9),
    ("grid_w", "8"), ("grid_w", 8.0), ("grid_w", 8.9),
    ("path_len", "5"), ("path_len", 5.0), ("path_len", 5.9),
    ("grid_h", True), ("grid_w", False), ("path_len", True),
    ("grid_h", []), ("grid_w", {}), ("path_len", object()),
])
def test_invalid_axis_overrides_are_rejected(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7, 0, difficulty="medium", **{axis: value})


@pytest.mark.parametrize("value", (7, None, True, "ignored"))
def test_unknown_override_names_are_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7, 0, difficulty="medium", unknown_axis=value)


@pytest.mark.parametrize("difficulty", BANDS)
def test_observer_reports_pixels_and_strict_hook_accepts_generated_inputs(difficulty):
    for sample_index in range(20):
        grid = GEN.generate(12345, sample_index, difficulty=difficulty)
        independent = assert_induced_endpoint_path(grid)
        original = copy.deepcopy(grid)
        observed = GEN.observe_overrides(grid)
        assert all(type(observed[key]) is int and observed[key] == value
                   for key, value in independent.items())
        assert strict_accepts(grid)
        assert grid == original


def test_observer_counts_canonical_total_path_lengths_including_seeds():
    expected_lengths = (7, 12, 19)
    assert tuple(sum(value != 0 for row in pair["input"] for value in row)
                 for pair in CANONICAL) == expected_lengths
    for pair, length in zip(CANONICAL, expected_lengths):
        observed = GEN.observe_overrides(copy.deepcopy(pair["input"]))
        assert observed["grid_h"] == len(pair["input"])
        assert observed["grid_w"] == len(pair["input"][0])
        assert observed["path_len"] == length
