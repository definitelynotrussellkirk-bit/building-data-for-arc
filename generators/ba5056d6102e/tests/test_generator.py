"""Task-local regression tests for the Boolean-intersection curriculum."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    intersection_output,
    occupancy_counts,
    panel_colors,
)
from reference_probe import load_generator  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_authority_is_pinned() -> None:
    assert gen.RULE_HASH == "1586ec3843ec"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: str(len(pair["input"])))
def test_canonical_examples_are_accepted_and_match_independent_oracle(pair: dict) -> None:
    assert gen.self_check(pair["input"]) == []
    assert intersection_output(pair["input"]) == pair["output"]
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_in_every_band(band: str | None) -> None:
    requested = {
        "half_h": 7,
        "grid_w": 14,
        "top_color": 1,
        "bottom_color": 9,
        "support_style": "diagonal",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    for key in ("half_h", "grid_w", "top_color", "bottom_color"):
        assert observed[key] == requested[key]
    assert len(grid) == 2 * requested["half_h"] + 1
    assert len(grid[0]) == requested["grid_w"]
    assert panel_colors(grid) == (1, 9)


def test_unknown_override_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, misspelled_axis=3)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_has_canonical_and_generalized_support_in_each_band(band: str) -> None:
    grids = [gen.generate(8801, index, difficulty=band) for index in range(20)]
    strict = [gen.strict_canonical_like(grid) == [] for grid in grids]
    assert any(strict)
    assert not all(strict)
    assert {gen.schedule_profile(8801, i, band) for i in range(20)} == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_exposes_complete_boolean_truth_table(band: str | None) -> None:
    for index in range(64):
        grid = gen.generate(4100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert all(count > 0 for count in occupancy_counts(grid).values())
        expected = intersection_output(grid)
        assert any(value == 8 for row in expected for value in row)
        assert any(value == 0 for row in expected for value in row)


def test_support_style_axis_is_effective() -> None:
    common = dict(half_h=7, grid_w=14, top_color=1, bottom_color=9)
    grids = {
        style: gen.generate(91, 8, support_style=style, **common)
        for style in ("scattered", "clustered", "striped", "diagonal")
    }
    assert len({repr(grid) for grid in grids.values()}) == len(grids)
    assert all(gen.self_check(grid) == [] for grid in grids.values())


def test_declared_rivals_are_real_counterexamples() -> None:
    required = {"union", "xor", "top_only", "bottom_only", "canonical_colors_only"}
    assert required <= set(gen.SEMANTIC_RIVALS)
    assert required <= set(gen.LESSON_COMPETITORS)
    grid = gen.generate(
        313, 1, half_h=6, grid_w=11,
        top_color=1, bottom_color=9, support_style="clustered",
    )
    authority = intersection_output(grid)
    for name in required:
        assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != authority, name


def test_canonical_palette_shortcut_fits_public_pairs_but_not_generalized_data() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_colors_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = gen.generate(99, 1, top_color=1, bottom_color=9)
    assert shortcut(grid) != intersection_output(grid)


@pytest.mark.parametrize("start", range(8))
def test_each_three_demo_window_refutes_every_declared_competitor(start: int) -> None:
    demos = []
    for offset in range(3):
        grid = gen.generate(7331, start + offset, difficulty="hard")
        demos.append({"input": grid, "output": intersection_output(grid)})
    query_grid = gen.generate(7331, start + 3, difficulty="hard")
    query = {"input": query_grid, "output": intersection_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


@pytest.mark.parametrize(
    "mutation",
    ["break_divider", "extra_top_color", "same_panel_color", "reserved_input_8", "remove_truth_state"],
)
def test_self_check_rejects_destructive_mutations(mutation: str) -> None:
    grid = gen.generate(43, 6, half_h=5, grid_w=8, top_color=2, bottom_color=3)
    divider = len(grid) // 2
    if mutation == "break_divider":
        grid[divider][0] = 0
    elif mutation == "extra_top_color":
        grid[0][0] = 4 if grid[0][0] != 4 else 6
    elif mutation == "same_panel_color":
        for r in range(divider + 1, len(grid)):
            grid[r] = [2 if value else 0 for value in grid[r]]
    elif mutation == "reserved_input_8":
        grid[0][0] = 8
    elif mutation == "remove_truth_state":
        top, bottom = grid[:divider], grid[divider + 1 :]
        for r in range(divider):
            for c in range(len(grid[0])):
                if top[r][c] != 0 and bottom[r][c] == 0:
                    bottom[r][c] = 3
    assert gen.self_check(grid)


def test_replay_is_deterministic_and_call_order_independent() -> None:
    expected = gen.generate(1201, 17, difficulty="hard")
    for index in range(100):
        gen.generate(index, index * 7, difficulty="easy")
    assert gen.generate(1201, 17, difficulty="hard") == expected
