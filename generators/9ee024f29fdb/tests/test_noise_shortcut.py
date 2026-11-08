"""Regression for the retained border-marker lattice shortcut audit."""
from __future__ import annotations

import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import authority_output, load_generator  # noqa: E402


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def border_marker_rival(grid):
    """Wrong rule from retained audit review-ce9b3fd21b6572c7.

    When lattice noise is visible, it treats nonzero cells in column 0 and row
    0 as the row/column selectors instead of using fixed period-four indices.
    """
    height, width = len(grid), len(grid[0])
    lattice_has_noise = any(
        grid[r][c] != 0
        for r in range(height)
        for c in range(width)
        if r % 4 == 0 or c % 4 == 0
    )
    if lattice_has_noise:
        erased_rows = {0} | {r for r in range(height) if grid[r][0] != 0}
        erased_cols = {0} | {c for c in range(width) if grid[0][c] != 0}
    else:
        erased_rows = {r for r in range(height) if r % 4 == 0}
        erased_cols = {c for c in range(width) if c % 4 == 0}
    return [
        [
            0 if r in erased_rows or c in erased_cols or value == 8 else 2
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def test_noisy_profile_refutes_border_marker_lattice_shortcut() -> None:
    """At least one deterministic noisy sample must falsify the audit rival."""
    witnessed = []
    for offset in range(12):
        sample_index = 2 * offset + 1  # joint_counterexample schedule positions
        grid = gen.generate(
            910_000 + offset,
            sample_index,
            difficulty="hard",
            grid_h=13,
            grid_w=13,
            lattice_noise=True,
            decoy_palette_size=1,
        )
        assert gen.self_check(grid) == []
        if border_marker_rival(grid) != authority_output(grid):
            witnessed.append((910_000 + offset, sample_index))
    assert witnessed, (
        "all generated noisy samples still encode periodic rows only in column 0 "
        "and periodic columns only in row 0"
    )
