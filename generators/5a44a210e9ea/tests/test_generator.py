"""Task-local regression suite for palette-depth frame semantics."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    canonical_pairs,
    load_generator,
    no_palette_reuse_rival,
    observed_axes,
    oracle_output,
    paint_every_component_rival,
    prefix_palette_rival,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_canonical_oracle_contract():
    assert gen.RULE_HASH == "8d815468fa81"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)
    assert all(oracle_output(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_declared_axis_is_exact_and_observable_in_every_band(band):
    options = {
        "grid_h": 15,
        "grid_w": 10,
        "palette_size": 5,
        "palette_layout": "gapped",
        "scene_kind": "touching_decoy",
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 11),
        ("grid_h", 19),
        ("grid_w", 9),
        ("grid_w", 19),
        ("palette_size", 1),
        ("palette_size", 6),
        ("palette_layout", "diagonal"),
        ("scene_kind", "all_objects"),
        ("grid_h", True),
        ("grid_w", 12.0),
        ("palette_size", "3"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_touching_decoy_is_connected_but_not_a_frame_and_is_erased():
    grid = gen.generate(
        22,
        4,
        grid_h=15,
        grid_w=10,
        palette_size=3,
        palette_layout="packed",
        scene_kind="touching_decoy",
    )
    info = analyze(grid)
    assert len(info["frames"]) == 1
    assert len(info["nonframes"]) == 1
    assert oracle_output(grid) != paint_every_component_rival(grid)
    out = oracle_output(grid)
    assert all(out[r][c] == 0 for cells in info["nonframes"] for r, c in cells)


def test_gapped_palette_defeats_contiguous_prefix_shortcut():
    grid = gen.generate(
        31,
        2,
        grid_h=13,
        grid_w=12,
        palette_size=3,
        palette_layout="gapped",
        scene_kind="clean",
    )
    assert observed_axes(grid)["palette_layout"] == "gapped"
    assert oracle_output(grid) != prefix_palette_rival(grid)


def test_more_frames_than_palette_reuses_last_palette_colour():
    witnesses = [gen.generate(43, index) for index in range(16)]
    grid = next(
        grid
        for grid in witnesses
        if len(analyze(grid)["frames"]) > analyze(grid)["palette_size"]
    )
    assert oracle_output(grid) != no_palette_reuse_rival(grid)


def test_declared_schedule_covers_all_training_roles_in_each_four_examples():
    expected = {
        "palette_reuse",
        "canonical_decoy",
        "gapped_palette",
        "combined_stress",
    }
    assert set(gen.SCHEDULE_PROFILES) == expected
    for offset in range(8):
        names = {gen.schedule_profile(99, offset + step, "medium") for step in range(4)}
        assert names == expected


def test_every_query_rotation_of_five_pair_schedule_is_identifiable():
    """No pair should be the sole evidence against a declared wrong rule."""
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(4):
            pairs = []
            for step in range(5):
                grid = gen.generate(8_000 + 100 * band_index + start, start + step, difficulty=band)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band, start, query_index,
                    gen.lesson_identifiable(demos, query),
                )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_each_named_semantic_witness(band):
    seen_profiles = set()
    seen_witnesses = {name: False for name in gen.SEMANTIC_WITNESSES}
    for index in range(64):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=band)
        seen_profiles.add(gen.schedule_profile(700 + index, index, band))
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            seen_witnesses[name] |= bool(predicate(grid))
    assert seen_profiles == set(gen.SCHEDULE_PROFILES)
    assert all(seen_witnesses.values()), seen_witnesses


def test_named_rivals_fit_the_expected_canonical_subset_and_have_counterexamples():
    pairs = canonical_pairs()
    # These two shortcuts really do survive the packed/no-reuse canonical cases.
    assert all(prefix_palette_rival(pair["input"]) == pair["output"] for pair in pairs)
    assert all(no_palette_reuse_rival(pair["input"]) == pair["output"] for pair in pairs)
    # The malformed-object shortcut is already refuted by train3 and test0.
    assert any(paint_every_component_rival(pair["input"]) != pair["output"] for pair in pairs)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert callable(rival), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        assert witness_name in gen.SEMANTIC_WITNESSES
        assert rival_names
        assert all(name in gen.SEMANTIC_RIVALS for name in rival_names)


@pytest.mark.parametrize(
    "mutation",
    [
        "empty_palette",
        "duplicate_palette_colour",
        "foreign_body_colour",
        "break_outer_frame",
        "add_isolated_blue_pixel",
        "ragged",
        "bool_cell",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        88,
        3,
        grid_h=13,
        grid_w=12,
        palette_size=3,
        palette_layout="packed",
        scene_kind="clean",
    )
    grid = deepcopy(grid)
    if mutation == "empty_palette":
        grid[0] = [0] * len(grid[0])
    elif mutation == "duplicate_palette_colour":
        grid[0][1] = grid[0][0]
    elif mutation == "foreign_body_colour":
        grid[2][2] = 9
    elif mutation == "break_outer_frame":
        grid[1][0] = 0
    elif mutation == "add_isolated_blue_pixel":
        grid[2][2] = 1
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(12)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generator_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(500, index) for index in range(12))
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]
