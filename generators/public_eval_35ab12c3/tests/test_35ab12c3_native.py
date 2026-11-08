"""Behavioral contract for public parent 35ab12c3."""
from __future__ import annotations

from pathlib import Path
import copy
import importlib.util
import json
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "shared/data/raw/arc-agi_evaluation_challenges.json").exists())


def load_generator():
    path = HOME / "generator.py"
    assert path.exists(), "generator.py has not been authored"
    spec = importlib.util.spec_from_file_location("_public_eval_35ab12c3_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def official_pairs():
    challenges = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())
    solutions = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())
    parent = challenges["35ab12c3"]
    return parent["train"] + [
        {"input": pair["input"], "output": output}
        for pair, output in zip(parent["test"], solutions["35ab12c3"])
    ]


def test_python_rule_matches_all_official_labels():
    g = load_generator()
    for pair in official_pairs():
        assert g.solve(pair["input"], "all_8") == pair["output"]


def test_angular_order_avoids_aligned_interior_chords():
    g = load_generator()
    grid = [[0] * 9 for _ in range(9)]
    # Hexagon vertices. The same-column and same-row opposite vertices are
    # aligned chords, not consecutive angular neighbors, so they stay blank.
    for r, c in [(1, 4), (1, 5), (4, 1), (4, 8), (7, 4), (7, 5)]:
        grid[r][c] = 3
    out = g.solve(grid)
    assert out[4][4] == 0
    assert out[4][5] == 0
    assert out[2][3] == 3
    assert out[6][6] == 3


def test_singleton_shadow_consumes_completed_target_and_preserves_occupied_cells():
    g = load_generator()
    grid = [[0] * 10 for _ in range(10)]
    # Target 6 is a V. Marker 4 is one row above the left endpoint.
    for r, c in [(2, 5), (6, 1), (6, 9)]:
        grid[r][c] = 6
    grid[5][1] = 4
    original = copy.deepcopy(grid)
    out = g.solve(grid)
    # The marker copies the completed V, not merely the three seed cells.
    assert [out[r][c] for r, c in [(1, 5), (2, 4), (3, 3), (4, 2), (5, 1)]] == [4] * 5
    assert [out[r][c] for r, c in [(2, 6), (3, 7), (4, 8), (5, 9)]] == [4] * 4
    # Shifted pixels that collide with the source keep the source color.
    assert out[2][5] == 6
    assert grid == original


def test_orthogonal_setting_omits_diagonal_edges_but_keeps_axis_edges_and_shadow_stage():
    g = load_generator()
    grid = [[0] * 10 for _ in range(10)]
    for r, c in [(2, 5), (6, 1), (6, 9)]:
        grid[r][c] = 6
    grid[5][1] = 4
    full = g.solve(grid, "all_8")
    orth = g.solve(grid, "orthogonal")
    assert full != orth
    assert full[3][4] == 6 and orth[3][4] == 0
    assert all(orth[6][c] == 6 for c in range(1, 10))
    # B still consumes A's orthogonal completion: the shifted horizontal edge appears.
    assert all(orth[5][c] == 4 for c in range(2, 10))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 31],
        [[0], [0, 0]],
        [[True]],
        [[10]],
    ],
)
def test_rejects_malformed_grids(grid):
    g = load_generator()
    with pytest.raises(ValueError):
        g.solve(grid)
