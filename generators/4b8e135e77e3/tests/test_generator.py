"""Task-local regression suite for the k-step orbit sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, load_generator, observed, orbit_output, racket_outputs

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {"grid_h", "grid_w", "k_rot", "shape_size", "palette_kind", "tally_layout"}


def test_metadata_pins_authority_and_exposes_only_observable_axes():
    assert gen.RULE_HASH == "a44e14a9fb6c"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert orbit_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_joint_overrides_are_honored_in_every_band(band):
    options = {
        "grid_h": 7,
        "grid_w": 7,
        "k_rot": 4,
        "shape_size": 8,
        "palette_kind": "multicolor",
        "tally_layout": "scattered",
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert orbit_output(grid) != orbit_output(grid, tally_mode="prefix")
    assert orbit_output(grid) != orbit_output(grid, shape_mode="six_only")


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 6), ("grid_h", 17), ("grid_w", 6), ("grid_w", 19),
    ("k_rot", 0), ("k_rot", 5), ("shape_size", 1), ("shape_size", 9),
    ("palette_kind", "warm"), ("tally_layout", "random"),
    ("grid_h", True), ("k_rot", 2.5), ("shape_size", "3"),
])
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_deterministic_and_teaches_both_shortcuts(band):
    profiles = set()
    values = {name: set() for name in EXPECTED_AXES}
    for index in range(96):
        grid = gen.generate(2100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(2100 + index, index, difficulty=band)
        stats = observed(grid)
        assert stats == gen.observe_overrides(grid)
        for name, value in stats.items():
            values[name].add(value)
        profiles.add((stats["grid_h"], stats["grid_w"], stats["palette_kind"]))
        original = deepcopy(grid)
        assert orbit_output(grid) != grid
        assert grid == original
    assert any(h in {7, 9} and w in {7, 9} and palette == "canonical" for h, w, palette in profiles)
    assert values["k_rot"] >= {2, 3, 4}
    assert values["tally_layout"] == {"prefix", "scattered"}
    assert values["palette_kind"] == {"canonical", "monochrome", "multicolor"}
    assert len(values["grid_h"]) >= 4 and len(values["grid_w"]) >= 4
    assert len(values["shape_size"]) >= 4


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_two_demo_window_refutes_each_declared_competitor(band):
    for start in range(24):
        demos = [gen.generate(700 + start, start + offset, difficulty=band) for offset in range(2)]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(grid) != orbit_output(grid) for grid in demos), (band, start, name)


def _palette_gated_tally_rival(grid):
    noncanonical = any(value not in (0, 1, 6, 9) for row in grid for value in row)
    return orbit_output(grid, tally_mode="prefix" if noncanonical else "count")


def _layout_gated_shape_rival(grid):
    ones = [column for column, value in enumerate(grid[0]) if value == 1]
    scattered = ones != list(range(len(ones)))
    return orbit_output(grid, shape_mode="six_only" if scattered else "all")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_two_demo_window_refutes_cross_axis_gated_shortcuts(band):
    rivals = {
        "palette_gated_tally": _palette_gated_tally_rival,
        "layout_gated_shape": _layout_gated_shape_rival,
    }
    for start in range(24):
        demos = [gen.generate(1700 + start, start + offset, difficulty=band) for offset in range(2)]
        for name, rival in rivals.items():
            assert any(rival(grid) != orbit_output(grid) for grid in demos), (band, start, name)


def test_declared_shortcuts_fit_every_canonical_pair():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


@pytest.mark.parametrize("palette", ["monochrome", "multicolor"])
def test_noncanonical_color_witness_is_a_genuine_rival_counterexample(palette):
    grid = gen.generate(91, 4, palette_kind=palette, tally_layout="prefix")
    assert gen.SEMANTIC_WITNESSES["noncanonical_shape_color"](grid)
    assert gen.SEMANTIC_RIVALS["color6_only"](grid) != orbit_output(grid)


def test_scattered_tally_witness_is_a_genuine_rival_counterexample():
    grid = gen.generate(92, 5, k_rot=4, tally_layout="scattered", palette_kind="canonical")
    assert gen.SEMANTIC_WITNESSES["scattered_tally"](grid)
    assert gen.SEMANTIC_RIVALS["prefix_tally_only"](grid) != orbit_output(grid)


@pytest.mark.parametrize("mutation", ["erase_tally", "extra_anchor", "shape_in_row0", "one_below_row0", "clipped_rotation", "unknown_color"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 3, grid_h=9, grid_w=9, k_rot=3, shape_size=4)
    if mutation == "erase_tally":
        grid[0] = [0] * len(grid[0])
    elif mutation == "extra_anchor":
        grid[1][0] = 9
    elif mutation == "shape_in_row0":
        grid[0][-1] = 6
    elif mutation == "one_below_row0":
        grid[1][0] = 1
    elif mutation == "clipped_rotation":
        ar, ac = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
        grid[ar - 3][ac] = 6
    elif mutation == "unknown_color":
        grid[1][0] = 10
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = ("import sys,json;sys.path.insert(0,sys.argv[1]);"
              "from reference_probe import load_generator;"
              "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))" )
    results = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output([sys.executable, "-B", "-c", script, str(HOME / "workspace")], env=env, text=True))
    assert results[0] == results[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(24)]
    assert racket_outputs(grids) == [orbit_output(grid) for grid in grids]
