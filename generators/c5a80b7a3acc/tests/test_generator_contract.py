"""Pixel-observable regressions for the public shape-set generator contract.

Run directly from the repository or from the copied task_tests runtime. These
checks deliberately avoid private generator helpers and arbitrary RNG snapshots.
"""
from copy import deepcopy
import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest

# The local repository puts the public runtime helpers under shared/runtime;
# portable task runtimes also expose them at their root.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break
from reviewer_support import canonical_pairs, find_root

TASK_ID = "c5a80b7a3acc"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("contract_generator_c5a80b7a3acc", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")
TEXTURES = ("mixed", "and_mode", "xor_mode", "identical", "disjoint", "no_marker")


def components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        todo = [remaining.pop()]
        component = set(todo)
        while todo:
            r, c = todo.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        result.append(component)
    return result


def normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r-top, c-left) for r, c in cells}


def shapes(grid):
    a, b = components(grid, 2), components(grid, 3)
    assert len(a) == len(b) == 1, "source objects must survive placement as single components"
    return normalize(a[0]), normalize(b[0])


def observed(grid):
    a, b = shapes(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "core_size": len(a & b), "marker": int(any(7 in row for row in grid))}


def set_output(grid):
    a, b = shapes(grid)
    cells = a & b if any(7 in row for row in grid) else a ^ b
    if not cells:
        return [[0]]
    cells = normalize(cells)
    return [[8 if (r, c) in cells else 0
             for c in range(max(c for _, c in cells)+1)]
            for r in range(max(r for r, _ in cells)+1)]


def assert_lawful(grid):
    assert isinstance(grid, list) and 1 <= len(grid) <= 30
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert 1 <= len(grid[0]) <= 30
    assert all(type(value) is int and value in {0, 2, 3, 7, 9}
               for row in grid for value in row)
    shapes(grid)
    assert gen.self_check(grid) == []


def fixture_grid(a, b, marker=0, height=8, width=8):
    grid = [[0]*width for _ in range(height)]
    for r, c in a:
        grid[r+1][c+1] = 2
    for r, c in b:
        grid[r+4][c+4] = 3
    if marker:
        grid[0][0] = 7
    return grid


def test_canonical_authority_and_inputs_remain_supported():
    assert getattr(gen, "RULE_HASH", None) == "db99a498afde"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    for pair in pairs:
        assert_lawful(pair["input"])
        assert set_output(pair["input"]) == pair["output"]


def test_marker_placement_regression_seed_799():
    # Baseline 2.3.0 overwrites the bridge cell (10, 7) of its color-2
    # source with the marker, splitting that object in two.
    grid = gen.generate(799, 0, marker=1)
    assert_lawful(grid)
    assert observed(grid)["marker"] == 1


@pytest.mark.parametrize("band", BANDS)
def test_every_advertised_dimension_is_exact_in_every_band(band):
    for height, width in product(range(8, 17), repeat=2):
        grid = gen.generate(1729, height*17+width, difficulty=band,
                            grid_h=height, grid_w=width, core_size=3, marker=1)
        assert_lawful(grid)
        assert observed(grid) == dict(grid_h=height, grid_w=width, core_size=3, marker=1)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("texture", TEXTURES)
def test_supported_joint_axis_matrix_is_constructive(band, texture):
    # Exhaustive for this boundary/midpoint dimension matrix and all exact
    # overlap, marker and texture controls. No rejection/resampling escape.
    for height, width, core, marker in product((8, 12, 16), (8, 12, 16), range(7), (0, 1)):
        conflict = ((texture == "and_mode" and marker == 0)
                    or (texture in {"xor_mode", "no_marker"} and marker == 1)
                    or (texture == "disjoint" and core > 0)
                    or (texture == "identical" and core == 0))
        options = dict(grid_h=height, grid_w=width, core_size=core,
                       marker=marker, texture=texture)
        if conflict:
            with pytest.raises(ValueError):
                gen.generate(409, 3, difficulty=band, **options)
            continue
        grid = gen.generate(409, 3, difficulty=band, **options)
        assert_lawful(grid)
        actual = observed(grid)
        assert actual == {k: options[k] for k in actual}, options
        assert gen.observe_overrides(grid) == actual
        a, b = shapes(grid)
        if texture == "identical":
            assert a == b
        if texture == "disjoint":
            assert not a & b
        if texture == "no_marker":
            assert not {7, 9} & {value for row in grid for value in row}


@pytest.mark.parametrize("texture,marker", [("and_mode", 1), ("xor_mode", 0), ("no_marker", 0)])
def test_texture_without_marker_override_selects_branch(texture, marker):
    for seed in range(24):
        grid = gen.generate(seed, 19, texture=texture)
        assert_lawful(grid)
        assert observed(grid)["marker"] == marker
        if texture == "no_marker":
            assert not {7, 9} & {value for row in grid for value in row}


@pytest.mark.parametrize("options", [
    {"unknown_axis": 1}, {"texture": "unknown"}, {"texture": True},
    {"texture": None}, {"grid_h": 7}, {"grid_h": 17}, {"grid_w": 7},
    {"grid_w": 17}, {"core_size": -1}, {"core_size": 7},
    {"marker": -1}, {"marker": 2},
] + [{key: value} for key in ("grid_h", "grid_w", "core_size", "marker")
     for value in (True, False, 1.5, "1", None)])
def test_invalid_axis_controls_are_rejected(options):
    with pytest.raises(ValueError):
        gen.generate(31, 8, **options)


@pytest.mark.parametrize("difficulty", ["extreme", "", 1, 0.5, True, [], {}])
def test_unsupported_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("marker", [0, 1])
def test_empty_set_operation_outputs_are_lawful(marker):
    if marker:
        # Both bounding minima are zero although neither shape occupies
        # (0, 0). Their connected cell sets have no common offset.
        a = {(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)}
        b = {(0, 1), (1, 1), (1, 0)}
    else:
        a = b = {(0, 0), (0, 1), (1, 0)}
    grid = fixture_grid(a, b, marker)
    assert set_output(grid) == [[0]]
    assert_lawful(grid)


@pytest.mark.parametrize("marker", [0, 1])
def test_observer_reads_pixels_and_validator_does_not_mutate(marker):
    grid = fixture_grid({(0, 0), (1, 0)}, {(0, 0), (0, 1)}, marker)
    original = deepcopy(grid)
    assert gen.observe_overrides(grid) == dict(grid_h=8, grid_w=8, core_size=1, marker=marker)
    assert gen.self_check(grid) == []
    assert grid == original


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 2]],
    [[0]*31 for _ in range(8)], [[0]*8 for _ in range(31)],
    [[True, 3]], [[2.0, 3]], [["2", 3]], [[2, 3, 1]], [[2, 3, 8]],
    [[2, 3, -1]], [[2, 3, 10]], [[2]], [[3]], [[2, 0, 2, 3]]])
def test_malformed_inputs_return_diagnostics(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


def test_validator_accepts_legal_noise_palette_and_maximum_dimensions():
    grid = fixture_grid({(0, 0)}, {(0, 0)}, marker=1, height=30, width=30)
    grid[29][29] = 9
    assert_lawful(grid)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("marker", [0, 1])
def test_source_areas_and_branch_population_do_not_encode_shortcuts(band, marker):
    areas_a, areas_b, orders, xor_parities, patterns = set(), set(), set(), set(), set()
    for index in range(128):
        grid = gen.generate(7200+index, index*7, difficulty=band, marker=marker)
        assert_lawful(grid)
        a, b = shapes(grid)
        areas_a.add(len(a)); areas_b.add(len(b))
        orders.add((len(a) > len(b)) - (len(a) < len(b)))
        xor_parities.add(len(a ^ b) % 2)
        patterns.add((frozenset(a), frozenset(b)))
    assert len(areas_a) >= 3 and len(areas_b) >= 3
    assert {-1, 1} <= orders, "each branch needs both source-cardinality orders"
    assert {0, 1} <= xor_parities, "equal-area-only shapes hide odd XOR outputs"
    assert len(patterns) >= 8


@pytest.mark.parametrize("band", BANDS)
def test_generation_is_deterministic_and_call_order_independent(band):
    options = dict(grid_h=8, grid_w=16, core_size=2, marker=1, texture="mixed")
    expected = gen.generate(87, 13, difficulty=band, **options)
    for index in range(20):
        gen.generate(index, index*3, difficulty=band)
    assert gen.generate(87, 13, difficulty=band, **options) == expected
    assert gen.generate(87, 13, difficulty=band, **dict(reversed(list(options.items())))) == expected
