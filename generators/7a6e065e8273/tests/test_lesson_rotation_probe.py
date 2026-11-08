"""Regression tests for the task-local cyclic lesson identifiability probe."""
from __future__ import annotations

import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import geometry_output, load_generator  # noqa: E402
from lesson_rotation_probe import analyze_instance  # noqa: E402


gen = load_generator()


def one_center(color: int, row: int, col: int) -> list[list[int]]:
    grid = [[0] * 8 for _ in range(8)]
    grid[row][col] = color
    return grid


def instance_from(grids: list[list[list[int]]]) -> dict:
    pairs = [{"input": grid, "output": geometry_output(grid)} for grid in grids]
    return {"train": pairs[:3], "test": pairs[3:]}


def test_rotation_probe_detects_single_nonfive_witness_becoming_query():
    instance = instance_from(
        [
            one_center(5, 2, 2),
            one_center(5, 2, 5),
            one_center(5, 5, 2),
            one_center(4, 5, 5),
        ]
    )
    report = analyze_instance(gen, instance)
    assert report["rotation_count"] == 4
    assert report["ambiguous_rotation_count"] == 1
    assert report["ambiguous_rotations"][0]["query_index"] == 3
    assert any(
        "only_color_five_centers" in name
        for name in report["ambiguous_rotations"][0]["surviving_rivals"]
    )


def test_rotation_probe_accepts_two_nonfive_witnesses():
    instance = instance_from(
        [
            one_center(5, 2, 2),
            one_center(3, 2, 5),
            one_center(5, 5, 2),
            one_center(4, 5, 5),
        ]
    )
    report = analyze_instance(gen, instance)
    assert report["rotation_count"] == 4
    assert report["ambiguous_rotation_count"] == 0
