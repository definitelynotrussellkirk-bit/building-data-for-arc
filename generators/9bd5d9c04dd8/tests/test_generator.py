"""Source-bound task regressions for 9bd5d9c04dd8."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    authority_paths,
    canonical_pairs,
    canonical_program,
    isolated_tiles,
    load_generator,
    make_grid,
    most_non_eight_rival,
    observed,
    oracle_output,
    shortcut_witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_inputs_are_lawful_and_outputs_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]


def test_active_authorities_are_exact_selected_canonical_source():
    expected = canonical_program()
    for path in authority_paths():
        payload = json.loads(path.read_text())
        assert payload["racket_target"]["target_code"] == expected, path


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 8, "grid_w": 9, "tile_count": 4, "fill_color": 6},
        {"grid_h": 16, "grid_w": 18, "tile_count": 2, "fill_color": 8},
    ],
)
def test_every_exact_axis_is_honored_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 17),
        ("grid_w", 8),
        ("grid_w", 19),
        ("tile_count", 1),
        ("tile_count", 5),
        ("fill_color", 1),
        ("fill_color", 10),
        ("grid_h", True),
        ("grid_w", 9.0),
        ("tile_count", "2"),
        ("fill_color", False),
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_refutes_shortcut(band):
    fill_colors = set()
    tile_counts = set()
    winners = set()
    shapes = set()
    for index in range(96):
        seed, sample_index = 2100 + index, index * 11 + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen._intended_output(grid) == oracle_output(grid)
        assert gen._most_non_eight_tile(grid) == most_non_eight_rival(grid)
        assert oracle_output(grid) != most_non_eight_rival(grid)
        assert gen.SEMANTIC_WITNESSES["non_eight_shortcut"](grid)
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        if sample_index % 2 == 0:
            assert (stats["grid_h"], stats["grid_w"]) == (9, 9)
        fill_colors.add(stats["fill_color"])
        tile_counts.add(stats["tile_count"])
        winners.add(json.dumps(oracle_output(grid)))
    assert 8 not in fill_colors
    assert len(fill_colors) >= 5
    assert len(winners) >= 24
    assert len(shapes) >= 18
    if band is None:
        assert tile_counts == {2, 3, 4}
    else:
        expected = {"easy": 2, "medium": 3, "hard": 4}[band]
        assert tile_counts == {expected}



def test_lawful_solid_output_is_explicitly_justified():
    text = getattr(gen, "SOLID_OUTPUT_JUSTIFICATION", "")
    assert len(text.strip()) >= 30
    grid = gen.generate(73, 5, grid_h=9, grid_w=9, tile_count=2, fill_color=2)
    assert gen.self_check(grid) == []


def test_canonical_fit_shortcut_has_exact_generated_counterexample():
    rival = gen.CANONICAL_SHORTCUTS["most_non_eight"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = shortcut_witness_input()
    assert gen.self_check(grid) == []
    intended = oracle_output(grid)
    shortcut = most_non_eight_rival(grid)
    assert intended == [[1, 1, 1], [1, 1, 2], [2, 2, 2]]
    assert shortcut == [[1, 2, 2], [2, 2, 2], [2, 2, 2]]
    assert intended != shortcut
    assert gen.SEMANTIC_WITNESSES["non_eight_shortcut"](grid)


def test_zero_blue_tile_and_diagonal_corner_contact_are_lawful():
    grid = make_grid([(0, 0, 0), (3, 3, 4)], fill=7)
    assert len(isolated_tiles(grid)) == 2
    assert gen.self_check(grid) == []
    assert oracle_output(grid) == [row[3:6] for row in grid[3:6]]


@pytest.mark.parametrize(
    "case",
    ["one_color_grid", "single_tile", "tied_counts", "stray_nonzero", "second_fill_color"],
)
def test_self_check_rejects_known_impostors(case):
    if case == "one_color_grid":
        grid = [[1] * 9 for _ in range(9)]
    elif case == "single_tile":
        grid = make_grid([(0, 0, 4)])
    elif case == "tied_counts":
        grid = make_grid([(0, 0, 4), (0, 4, 4)])
    elif case == "stray_nonzero":
        grid = make_grid([(0, 0, 2), (0, 4, 5)])
        grid[8][8] = 1
    else:
        grid = make_grid([(0, 0, 2), (0, 4, 5)])
        grid[1][1] = 3
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)], [[-1] * 9 for _ in range(9)]],
)
def test_self_check_reports_malformed_grids_without_raising(grid):
    assert gen.self_check(grid)


def test_oracle_and_observer_do_not_mutate_input():
    grid = gen.generate(42, 99)
    original = deepcopy(grid)
    assert gen._intended_output(grid) == oracle_output(grid)
    assert gen.observe_overrides(grid) == observed(grid)
    assert grid == original
