"""Behavioral contract for the repaired 95b47c355ae4 input sampler."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "95b47c355ae4"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_shift_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_6_cells": sum(value == 6 for row in grid for value in row),
        "n_5_cells": sum(value == 5 for row in grid for value in row),
    }


def components_of_five(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    sizes = []
    while cells:
        stack = [cells.pop()]
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in cells:
                    cells.remove(nxt)
                    stack.append(nxt)
        sizes.append(size)
    return tuple(sorted(sizes))


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "76edf9516933"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_6_cells", "n_5_cells"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_inputs_are_lawful_and_python_oracle_matches_labels():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "h,w,n6,n5",
    [(8, 8, 3, 3), (8, 10, 7, 12), (10, 8, 5, 11), (10, 10, 4, 8)],
)
def test_exact_joint_controls_are_realized_in_pixels(band, h, w, n6, n5):
    grid = gen.generate(
        712,
        5,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        n_6_cells=n6,
        n_5_cells=n5,
    )
    expected = {"grid_h": h, "grid_w": w, "n_6_cells": n6, "n_5_cells": n5}
    assert observed(grid) == expected
    assert gen.observe_overrides(grid) == expected
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "axes",
    [
        {"misspelled_axis": 1},
        {"grid_h": 7},
        {"grid_w": 11},
        {"n_6_cells": 2},
        {"n_6_cells": 8},
        {"n_5_cells": 2},
        {"n_5_cells": 13},
        {"grid_h": True},
        {"n_6_cells": 4.0},
        {"n_5_cells": "5"},
        {"texture": "legacy"},
        {"palette_kind": "warm"},
    ],
)
def test_invalid_and_retired_controls_fail_loudly(axes):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **axes)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_instances_obey_the_actual_rule_domain(band):
    for index in range(48):
        grid = gen.generate(1907, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1907, index, difficulty=band)
        h, w = len(grid), len(grid[0])
        sixes = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6}
        fives = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
        assert sixes and fives
        assert all(r + 1 < h and c + 1 < w for r, c in sixes)
        assert all((r + 1, c + 1) not in sixes | fives for r, c in sixes)
        assert all(
            (r + dr, c + dc) not in sixes
            for r, c in sixes
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
        output = gen._reference_output(grid)
        assert sum(value == 6 for row in output for value in row) == len(sixes)
        assert {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 5} == fives


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_recurs_on_canonical_profiles_and_varies_gray_topology(band):
    grids = [gen.generate(4301 + index, index, difficulty=band) for index in range(90)]
    shapes = {(len(grid), len(grid[0])) for grid in grids}
    n6_values = {observed(grid)["n_6_cells"] for grid in grids}
    n5_values = {observed(grid)["n_5_cells"] for grid in grids}
    topologies = {components_of_five(grid) for grid in grids}
    assert {(8, 8), (9, 9), (10, 10)} <= shapes
    assert {3, 5} <= n6_values
    assert {3, 7, 8, 9, 11} <= n5_values
    assert len(topologies) >= 5


def test_declared_competitors_are_real_and_each_generated_demo_refutes_them():
    assert gen.LESSON_COMPETITORS
    for index in range(24):
        grid = gen.generate(995, index)
        truth = gen._reference_output(grid)
        pair = {"input": grid, "output": truth}
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != truth, name
        assert gen.lesson_identifiable([pair], pair) == []


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 8 for _ in range(8)],
        [[False] * 8 for _ in range(8)],
        [[9] + [0] * 7 for _ in range(8)],
    ],
)
def test_validator_rejects_malformed_or_out_of_domain_grids(grid):
    assert gen.self_check(grid)


def test_validator_rejects_blocked_or_nonisolated_sources():
    grid = gen.generate(17, 2, grid_h=8, grid_w=8, n_6_cells=3, n_5_cells=3)
    sixes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]

    blocked = [row[:] for row in grid]
    r, c = sixes[0]
    blocked[r + 1][c + 1] = 5
    assert any("target" in reason for reason in gen.self_check(blocked))

    touching = [row[:] for row in grid]
    r, c = sixes[1]
    candidate = (r, c + 1) if c + 1 < len(grid[0]) - 1 else (r, c - 1)
    touching[candidate[0]][candidate[1]] = 6
    assert any("isolated" in reason for reason in gen.self_check(touching))

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_generated_scene_breaks_source_row_and_column_parity_shortcuts(band):
    for index in range(24):
        grid = gen.generate(8819 + index, index, difficulty=band)
        sources = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 6
        ]
        assert {r % 2 for r, _ in sources} == {0, 1}
        assert {c % 2 for _, c in sources} == {0, 1}
