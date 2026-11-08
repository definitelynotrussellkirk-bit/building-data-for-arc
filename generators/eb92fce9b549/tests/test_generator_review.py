"""Regression and semantic-contract tests for the eb92fce9b549 review."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, components, load_generator, observed, ranked_output

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_size": {"type": "int", "valid": "7..24"},
    "n_objects": {"type": "int", "valid": "2..4"},
    "layout": {"type": "str", "valid": "rings|scattered"},
    "foreground_color": {"type": "int", "valid": "1..9"},
}


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "45c25a11961c"
    assert set(gen.AXES) == set(EXPECTED_AXES)
    for name, expected in EXPECTED_AXES.items():
        assert gen.AXES[name]["type"] == expected["type"]
        assert gen.AXES[name]["valid"] == expected["valid"]
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.HELPFUL_TEXTURES == ()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{len(pair['input'])}x{len(pair['input'][0])}")
def test_canonical_examples_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert ranked_output(pair["input"], by="bbox") == pair["output"]
    assert gen.strict_canonical_like(pair["input"]) == []


def test_cell_count_shortcut_fits_every_canonical_pair():
    assert all(ranked_output(pair["input"], by="cells") == pair["output"] for pair in canonical_pairs())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_size": 7, "n_objects": 2, "layout": "rings", "foreground_color": 1},
        {"grid_size": 9, "n_objects": 3, "layout": "rings", "foreground_color": 9},
        {"grid_size": 13, "n_objects": 4, "layout": "rings", "foreground_color": 4},
        {"grid_size": 7, "n_objects": 2, "layout": "scattered", "foreground_color": 6},
        {"grid_size": 24, "n_objects": 4, "layout": "scattered", "foreground_color": 2},
    ],
)
def test_exact_overrides_are_pixel_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "options",
    [
        {"layout": "rings", "grid_size": 7, "n_objects": 3},
        {"layout": "rings", "grid_size": 8, "n_objects": 3},
        {"layout": "rings", "grid_size": 7, "n_objects": 4},
        {"layout": "rings", "grid_size": 12, "n_objects": 4},
    ],
)
def test_impossible_exact_ring_combinations_reject_with_structured_axes(options):
    with pytest.raises(ValueError) as caught:
        gen.generate(0, 0, **options)
    assert set(caught.value.incompatible_axes) == set(options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_size", 6),
        ("grid_size", 25),
        ("grid_size", True),
        ("grid_size", "7"),
        ("n_objects", 1),
        ("n_objects", 5),
        ("n_objects", 2.0),
        ("layout", "blob"),
        ("layout", 1),
        ("foreground_color", 0),
        ("foreground_color", 10),
        ("foreground_color", False),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_hard_band_small_pinned_ring_grid_falls_back_to_feasible_count():
    grid = gen.generate(18, 0, difficulty="hard", grid_size=7, foreground_color=7)
    assert observed(grid) == {
        "grid_size": 7,
        "n_objects": 2,
        "layout": "rings",
        "foreground_color": 7,
    }
    assert gen.self_check(grid) == []


def test_partial_overrides_adapt_unpinned_axes_without_silently_dropping_requests():
    cases = [
        ({"layout": "rings", "grid_size": 7}, {"layout": "rings", "grid_size": 7, "n_objects": 2}),
        ({"layout": "rings", "n_objects": 4}, {"layout": "rings", "n_objects": 4}),
        ({"grid_size": 7, "n_objects": 4}, {"grid_size": 7, "n_objects": 4, "layout": "scattered"}),
    ]
    for index, (overrides, expected_subset) in enumerate(cases):
        grid = gen.generate(41, index, **overrides)
        actual = observed(grid)
        assert all(actual[name] == value for name, value in expected_subset.items())
        assert gen.self_check(grid) == []


def test_scattered_layout_is_a_real_bbox_vs_cell_count_counterexample():
    grid = gen.generate(11, 2, grid_size=7, n_objects=4, layout="scattered", foreground_color=8)
    intended = ranked_output(grid, by="bbox")
    shortcut = ranked_output(grid, by="cells")
    assert intended != shortcut
    assert gen.SEMANTIC_WITNESSES["bbox_vs_cell_count"](grid)
    assert gen.SEMANTIC_RIVALS["cell_count_rank"](grid) == shortcut
    assert gen.CANONICAL_SHORTCUTS["cell_count_rank"](grid) == shortcut
    assert gen.LESSON_COMPETITORS["cell_count_rank"](grid) == shortcut


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_example_window_refutes_declared_shortcut(band):
    for start in range(24):
        demos = []
        for offset in range(3):
            grid = gen.generate(1009 + start, start + offset, difficulty=band)
            demos.append({"input": grid, "output": ranked_output(grid, by="bbox")})
        query_grid = gen.generate(1009 + start, start + 3, difficulty=band)
        query = {"input": query_grid, "output": ranked_output(query_grid, by="bbox")}
        assert gen.lesson_identifiable(demos, query) == []
        assert any(
            gen.LESSON_COMPETITORS["cell_count_rank"](pair["input"]) != pair["output"]
            for pair in demos
        )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_canonical_profile_supported_and_deterministic(band):
    layouts = set()
    sizes = set()
    colors = set()
    for index in range(80):
        grid = gen.generate(600 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(600 + index, index, difficulty=band)
        stats = observed(grid)
        layouts.add(stats["layout"])
        sizes.add(stats["grid_size"])
        colors.add(stats["foreground_color"])
        assert stats["grid_size"] in {7, 9, 11, 13, 15}
        assert len({value for row in grid for value in row}) == 2
    assert layouts == {"rings", "scattered"}
    assert len(sizes) >= 4
    assert len(colors) >= 7


def test_output_oracles_do_not_mutate_input():
    grid = gen.generate(71, 5, layout="scattered")
    before = deepcopy(grid)
    gen.SEMANTIC_RIVALS["cell_count_rank"](grid)
    assert grid == before


@pytest.mark.parametrize(
    "mutator",
    [
        lambda grid: grid.pop(),
        lambda grid: grid[0].pop(),
        lambda grid: grid[0].__setitem__(0, 10),
        lambda grid: [row.__setitem__(col, 0) for row in grid for col in range(len(row))],
    ],
)
def test_validator_rejects_destructive_mutations(mutator):
    grid = gen.generate(5, 1, layout="scattered", grid_size=9)
    mutator(grid)
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generation_is_python_hash_seed_independent():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
