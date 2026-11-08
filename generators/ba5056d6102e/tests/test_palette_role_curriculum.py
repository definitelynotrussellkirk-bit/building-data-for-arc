"""Regression tests for foreground-color role coverage in lessons."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    intersection_output,
    load_generator,
    panel_colors,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_every_default_three_demo_window_uses_color_3_in_top_role() -> None:
    for band in (None, "easy", "medium", "hard"):
        for start in range(8):
            grids = [
                gen.generate(7331, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            assert any(panel_colors(grid)[0] == 3 for grid in grids), (
                band,
                start,
                [panel_colors(grid) for grid in grids],
            )


def test_color_3_bottom_only_shortcut_is_declared_and_refuted() -> None:
    name = "color_3_bottom_only"
    assert name in gen.CANONICAL_SHORTCUTS
    assert name in gen.LESSON_COMPETITORS
    shortcut = gen.CANONICAL_SHORTCUTS[name]
    assert all(
        shortcut(deepcopy(pair["input"])) == pair["output"]
        for pair in canonical_pairs()
    )

    grid = gen.generate(
        991,
        2,
        difficulty="hard",
        top_color=3,
        bottom_color=9,
        support_style="clustered",
    )
    authority = intersection_output(grid)
    assert shortcut(deepcopy(grid)) != authority
    assert gen.SEMANTIC_WITNESSES["top_color_3"](grid)
    assert name in gen.WITNESS_RIVALS["top_color_3"]
