"""Independent domain and Racket-law regressions for main-diagonal completion.

Run through the packet's run_with_racket.py wrapper or the public task_tests
stage. Root discovery deliberately supports both the library and staged layout.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "57488f2a7c15"
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")


@pytest.fixture(scope="module")
def generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("symmetry_domain_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_square_integer_grid(grid):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def conflicting_orbits(grid):
    """An unordered transpose pair cannot contain two different source colors."""
    return [
        ((r, c), grid[r][c], (c, r), grid[c][r])
        for r in range(len(grid))
        for c in range(r + 1, len(grid))
        if grid[r][c] != 0 and grid[c][r] != 0 and grid[r][c] != grid[c][r]
    ]


@pytest.mark.parametrize("band", BANDS)
def test_generated_inputs_have_no_transpose_conflicts(generator, band):
    for seed in range(512):
        grid = generator.generate(seed=seed, sample_index=seed, difficulty=band)
        assert_square_integer_grid(grid)
        assert not conflicting_orbits(grid), (band, seed, grid, conflicting_orbits(grid))
        assert generator.self_check(grid, difficulty=band) == [], (band, seed, grid)
        assert any(grid[r][c] != grid[c][r]
                   for r in range(len(grid)) for c in range(r + 1, len(grid))), (band, seed)


def test_validator_rejects_conflicting_transpose_pair(generator):
    grid = [[0] * 5 for _ in range(5)]
    grid[0][1], grid[1][0], grid[3][2] = 2, 3, 7
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors, "contradictory source colors were accepted"
    assert all(isinstance(error, str) and error for error in errors)


def test_validator_allows_equal_transpose_pair_and_diagonal_sources(generator):
    grid = [[0] * 5 for _ in range(5)]
    grid[0][1] = grid[1][0] = 3
    grid[1][1], grid[4][2] = 6, 2
    assert not conflicting_orbits(grid)
    assert generator.self_check(grid) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        7,
        True,
        "012",
        {"grid": [[0, 1], [0, 0]]},
        ((0, 1), (0, 0)),
        [],
        [[]],
        [[0, 1], [0]],
        [[0, 1], None],
        [[0, 1], (0, 0)],
        [[0, 1], 3],
        [[0, True], [0, 0]],
        [[0, 1.0], [0, 0]],
        [[0, -1], [0, 0]],
        [[0, 10], [0, 0]],
        [[0, "1"], [0, 0]],
        [[0, 1, 0], [0, 0, 0]],
    ],
    ids=["none", "scalar", "bool-grid", "string-grid", "dict-grid", "tuple-grid",
         "empty", "empty-row", "ragged", "none-row", "tuple-row", "scalar-row",
         "bool-cell", "float-cell", "negative-cell", "ten-cell", "string-cell", "rectangle"],
)
def test_malformed_inputs_return_diagnostic_list(generator, grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) and error for error in errors)


def test_all_canonical_inputs_are_accepted(generator):
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs, "canonical coverage must not silently disappear"
    for pair in pairs:
        grid = pair["input"]
        assert_square_integer_grid(grid)
        assert not conflicting_orbits(grid), pair
        assert generator.self_check(grid) == [], pair


@pytest.fixture(scope="module")
def reference_evidence(generator):
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    cases = [(f"canonical-{p['variant']}-{p['split']}-{p['pair_index']}", p["input"])
             for p in pairs]
    cases.extend((f"{band}-{seed}", generator.generate(seed=seed, sample_index=seed,
                                                     difficulty=band))
                 for band in BANDS for seed in range(12))
    # Independent lawful boundary cases: reflected pairs, diagonal colors,
    # either source triangle, a singleton, and the closure's fixed points.
    cases.extend([
        ("equal-pair-and-source", [[0, 3, 0], [3, 6, 2], [0, 0, 0]]),
        ("upper-source", [[0, 0, 7], [0, 0, 0], [0, 0, 4]]),
        ("lower-source", [[1, 0, 0], [0, 0, 0], [9, 0, 0]]),
        ("diagonal-fixed-point", [[2, 0], [0, 8]]),
        ("empty-fixed-point", [[0, 0], [0, 0]]),
        ("singleton-fixed-point", [[5]]),
    ])
    inputs = [deepcopy(grid) for _, grid in cases]
    preserved = deepcopy(inputs)
    catalog = Catalog(root=ROOT)
    results = []
    # The public reference API accepts at most 64 inputs per invocation.
    for start in range(0, len(inputs), 64):
        report = catalog.apply(TASK_ID, inputs[start:start + 64], timeout=120)
        assert report["rule_hash_matches_catalog"], report
        assert len(report["results"]) == len(inputs[start:start + 64])
        for item in report["results"]:
            assert item["valid_output"], item
            assert_square_integer_grid(item["output"])
        results.extend(item["output"] for item in report["results"])
    assert inputs == preserved, "reference execution mutated caller-owned input"
    return cases, results, pairs


def test_racket_outputs_are_symmetric(reference_evidence):
    cases, outputs, _ = reference_evidence
    for (name, grid), output in zip(cases, outputs, strict=True):
        assert len(output) == len(grid), name
        assert all(output[r][c] == output[c][r]
                   for r in range(len(output)) for c in range(len(output))), (name, grid, output)


def test_racket_preserves_every_source_cell(reference_evidence):
    cases, outputs, _ = reference_evidence
    for (name, grid), output in zip(cases, outputs, strict=True):
        assert all(output[r][c] == value
                   for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0), (
                       name, grid, output)


def test_racket_completion_is_idempotent(reference_evidence):
    cases, outputs, _ = reference_evidence
    catalog = Catalog(root=ROOT)
    for start in range(0, len(outputs), 64):
        report = catalog.apply(TASK_ID, outputs[start:start + 64], timeout=120)
        assert report["rule_hash_matches_catalog"], report
        assert len(report["results"]) == len(outputs[start:start + 64])
        for index, item in enumerate(report["results"], start=start):
            assert item["valid_output"] and item["output"] == outputs[index], (cases[index], item)


def test_racket_matches_every_canonical_output(reference_evidence):
    _, outputs, pairs = reference_evidence
    assert outputs[:len(pairs)] == [pair["output"] for pair in pairs]
