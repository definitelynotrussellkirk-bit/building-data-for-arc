"""Focused regressions for generator 5383f0933057."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "5383f0933057"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.5383f0933057.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    grids = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row.get("train") or [])
            test = row.get("test")
            pairs.extend(test if isinstance(test, list) else [test])
            for pair in pairs:
                if isinstance(pair, dict) and pair.get("input"):
                    grids.append(pair["input"])
    return grids


def _has_color_tie(grid):
    regions = MODULE._regions(grid)
    owner = {
        cell: index for index, region in enumerate(regions) for cell in region
    }
    seeds = [
        (r, c, grid[r][c], owner[(r, c)])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 9)
    ]
    for (r, c), region_index in owner.items():
        if grid[r][c] != 0:
            continue
        local = [seed for seed in seeds if seed[3] == region_index]
        distance = min(abs(r - sr) + abs(c - sc) for sr, sc, _, _ in local)
        nearest_colors = {
            color
            for sr, sc, color, _ in local
            if abs(r - sr) + abs(c - sc) == distance
        }
        if len(nearest_colors) >= 2:
            return True
    return False


def test_accepts_all_canonical_inputs_and_border_seed_regression():
    canonical = _canonical_inputs()
    assert len(canonical) == 3
    assert all(MODULE.self_check(copy.deepcopy(grid)) == [] for grid in canonical)
    # The official test has a color-5 seed in the right border. The pre-repair
    # checker rejected it with "left/right border must be color-9 walls".
    assert canonical[-1][4][-1] == 5


def test_exact_override_axes_and_incompatible_pairs():
    grid = MODULE.generate(
        991,
        17,
        difficulty="hard",
        grid_h=6,
        grid_w=8,
        n_chambers=4,
        n_seeds=8,
        palette_size=6,
        border_seeds=1,
    )
    assert MODULE.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 8,
        "n_chambers": 4,
        "n_seeds": 8,
        "palette_size": 6,
        "border_seeds": 1,
    }
    with pytest.raises(ValueError, match="cannot seed"):
        MODULE.generate(1, 1, n_chambers=4, n_seeds=2)
    with pytest.raises(ValueError, match="exceeds n_seeds"):
        MODULE.generate(1, 1, n_seeds=2, palette_size=6)
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 1, div_rows=2)


def test_self_check_rejects_targeted_structural_impostors():
    valid = MODULE.generate(101, 7, difficulty="medium")
    assert MODULE.self_check(valid) == []

    no_walls = copy.deepcopy(valid)
    for row in no_walls:
        for c, value in enumerate(row):
            if value == 9:
                row[c] = 0
    assert any("walls" in error for error in MODULE.self_check(no_walls))

    no_seeds = copy.deepcopy(valid)
    for row in no_seeds:
        for c, value in enumerate(row):
            if value not in (0, 9):
                row[c] = 0
    assert any("seed" in error for error in MODULE.self_check(no_seeds))

    one_color = copy.deepcopy(valid)
    for row in one_color:
        for c, value in enumerate(row):
            if value not in (0, 9):
                row[c] = 2
    assert any("distinct seed colors" in error for error in MODULE.self_check(one_color))

    no_zeros = copy.deepcopy(valid)
    for row in no_zeros:
        for c, value in enumerate(row):
            if value == 0:
                row[c] = 2
    assert any("fillable zero" in error for error in MODULE.self_check(no_zeros))

    # A full wall creates a new open chamber on one side. Remove every seed
    # from that chamber; a palette-only checker would miss this oracle no-op.
    unseeded = MODULE.generate(
        202, 9, difficulty="easy", n_chambers=2, n_seeds=3, palette_size=2
    )
    regions = MODULE._regions(unseeded)
    assert len(regions) == 2
    for r, c in regions[0]:
        if unseeded[r][c] not in (0, 9):
            unseeded[r][c] = 0
    assert any("unseeded chamber" in error for error in MODULE.self_check(unseeded))


def test_ordinary_draws_link_tie_and_chamber_semantics():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(40):
            grid = MODULE.generate(
                50000 + 1000 * band_index + offset,
                200 + offset,
                difficulty=band,
            )
            assert MODULE.self_check(grid) == []
            assert _has_color_tie(grid)
            observed = MODULE.observe_overrides(grid)
            if observed["n_chambers"] > 1:
                assert MODULE._has_cross_chamber_rebuttal(grid)



def test_sequential_three_demo_schedule_identifies_chamber_rule():
    assert MODULE.EXAMPLES_NEEDED == 3
    for seed in range(24):
        demos = [MODULE.generate(seed, index) for index in range(3)]
        observed = [MODULE.observe_overrides(grid) for grid in demos]
        assert observed[0]["n_chambers"] > 1
        assert observed[2]["n_chambers"] > 1
        assert observed[1]["border_seeds"] == 1
        assert (observed[1]["grid_h"], observed[1]["grid_w"]) in {(6, 8), (7, 9)}
        assert MODULE._has_cross_chamber_rebuttal(demos[0])
        assert MODULE._has_cross_chamber_rebuttal(demos[2])

def test_replay_freshness_and_process_global_rng_state():
    random.seed(8675309)
    before = random.getstate()
    first = MODULE.generate(31337, 44, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(31337, 44, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
