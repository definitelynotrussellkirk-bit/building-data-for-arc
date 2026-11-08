"""Behavioral contract for public parent e12f9a14."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "shared/data/raw/arc-agi_evaluation_challenges.json").exists())


def load_generator():
    path = HOME / "generator.py"
    assert path.exists(), "generator.py has not been authored"
    spec = importlib.util.spec_from_file_location("_public_eval_e12f9a14_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def official_pairs():
    challenges = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())
    solutions = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())
    parent = challenges["e12f9a14"]
    return parent["train"] + [
        {"input": pair["input"], "output": output}
        for pair, output in zip(parent["test"], solutions["e12f9a14"])
    ]


def test_python_rule_matches_all_official_labels():
    g = load_generator()
    for index, pair in enumerate(official_pairs()):
        assert g.solve(pair["input"], "vector_sum") == pair["output"], index


def test_simple_frame_emits_from_each_missing_perimeter_cell():
    g = load_generator()
    grid = [[8] * 8 for _ in range(8)]
    # 4x4 frame at rows 2..5, cols 1..4 around a 2x2 color-4 core.
    for r, c in [(2, 1), (2, 2), (2, 4), (3, 1), (3, 4),
                 (4, 1), (5, 2), (5, 3), (5, 4)]:
        grid[r][c] = 3
    for r in (3, 4):
        for c in (2, 3):
            grid[r][c] = 4
    expected = [row[:] for row in grid]
    for r, c in [(2, 3), (1, 3), (0, 3),
                 (4, 4), (4, 5), (4, 6), (4, 7),
                 (5, 1), (6, 0)]:
        expected[r][c] = 4
    assert g.solve(grid) == expected


def test_crossing_diagonals_merge_into_parallel_vertical_bundle():
    g = load_generator()
    grid = g._synthetic_crossing_grid(12, 14, background=8, frame=3, colors=(9, 1))
    trace = g.trace(grid, "vector_sum")
    assert any(event["kind"] == "merge" and event["course"] == [1, 0] for event in trace["events"])
    output = trace["output"]
    # The two crossing rays do not swap through one another. After the event,
    # they continue as adjacent vertical tracks in their original colors.
    assert output[8][6] == 9
    assert output[8][7] == 1
    assert output[11][6] == 9
    assert output[11][7] == 1


def test_stop_variant_terminates_colliding_bundles():
    g = load_generator()
    grid = g._synthetic_crossing_grid(12, 14, background=8, frame=3, colors=(9, 1))
    merged = g.solve(grid, "vector_sum")
    stopped = g.solve(grid, "stop")
    assert merged != stopped
    assert merged[11][6] == 9 and stopped[11][6] == 8


def test_trace_ignores_collisions_whose_geometric_point_is_off_canvas():
    g = load_generator()
    for pair in official_pairs():
        height, width = len(pair["input"]), len(pair["input"][0])
        for event in g.trace(pair["input"], "vector_sum")["events"]:
            row2, col2 = event["point2"]
            assert 0 <= row2 <= 2 * (height - 1)
            assert 0 <= col2 <= 2 * (width - 1)


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
