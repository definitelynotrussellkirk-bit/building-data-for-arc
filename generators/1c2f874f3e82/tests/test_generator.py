"""Regression tests for the anchor-frame transform-copy generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    at_most_five_rival,
    canonical_pairs,
    color_cells,
    connected,
    first_marker_rival,
    fixed_four_rival,
    load_generator,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_canonical_pairs_match_independent_oracle_and_contract():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert rule_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {"grid_h": 10, "grid_w": 16, "source_cells": 7, "n_markers": 5}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 15),
        ("grid_w", 15),
        ("grid_w", 21),
        ("source_cells", 2),
        ("source_cells", 8),
        ("n_markers", 2),
        ("n_markers", 6),
        ("grid_h", True),
        ("source_cells", 4.0),
        ("n_markers", "4"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_difficulty_bands_are_not_dead():
    grids = [gen.generate(23, 11, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) > 1


def test_distribution_covers_canonical_profiles_and_semantic_witnesses():
    canonical_profiles = {(10, 18, 6), (12, 18, 6), (12, 19, 6)}
    for band in (None, "easy", "medium", "hard"):
        profiles = set()
        source_counts = set()
        marker_counts = set()
        fixed_four_witnesses = 0
        repeated_marker_witnesses = 0
        inputs = set()
        for index in range(160):
            grid = gen.generate(8000 + index, index * 13, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(8000 + index, index * 13, difficulty=band)
            stats = observed(grid)
            profiles.add((stats["grid_h"], stats["grid_w"], len({v for row in grid for v in row})))
            source_counts.add(stats["source_cells"])
            marker_counts.add(stats["n_markers"])
            fixed_four_witnesses += rule_output(grid) != fixed_four_rival(grid)
            repeated_marker_witnesses += rule_output(grid) != first_marker_rival(grid)
            inputs.add(repr(grid))
            assert connected(color_cells(grid, 2))
        assert profiles & canonical_profiles
        assert {3, 4, 5, 6, 7} <= source_counts
        assert {3, 4, 5} <= marker_counts
        assert fixed_four_witnesses >= 100
        assert repeated_marker_witnesses >= 100
        assert len(inputs) >= 150


def test_fixed_four_shortcut_fits_demos_but_fails_query():
    pairs = canonical_pairs()
    demos = [p for p in pairs if p["split"] == "train"]
    query = next(p for p in pairs if p["split"] == "test")
    assert all(len(color_cells(p["input"], 2)) == 4 for p in demos)
    assert len(color_cells(query["input"], 2)) == 5
    assert all(fixed_four_rival(p["input"]) == p["output"] for p in demos)
    assert fixed_four_rival(query["input"]) != query["output"]
    assert gen.LESSON_COMPETITORS["fixed_four_source_cells"](query["input"]) == fixed_four_rival(query["input"])
    assert all(at_most_five_rival(p["input"]) == p["output"] for p in pairs)
    assert "at_most_five_source_cells" in gen.CANONICAL_SHORTCUTS
    assert "first_marker_only" in gen.CANONICAL_SHORTCUTS


def test_semantic_contract_and_lesson_gate_have_real_counterexamples():
    witness = gen.generate(31, 8, source_cells=7, n_markers=5)
    intended = rule_output(witness)
    assert gen.SEMANTIC_WITNESSES["source_more_than_four"](witness)
    assert gen.SEMANTIC_WITNESSES["source_more_than_five"](witness)
    assert gen.SEMANTIC_WITNESSES["repeated_marker_color"](witness)
    assert gen.SEMANTIC_RIVALS["fixed_four_source_cells"](witness) == fixed_four_rival(witness) != intended
    assert gen.SEMANTIC_RIVALS["at_most_five_source_cells"](witness) == at_most_five_rival(witness) != intended
    assert gen.SEMANTIC_RIVALS["first_marker_only"](witness) == first_marker_rival(witness) != intended

    ambiguous_query = {"input": witness, "output": intended}
    four_cell_demo = gen.generate(99, 1, source_cells=4, n_markers=3)
    ambiguous = gen.lesson_identifiable([{"input": four_cell_demo, "output": rule_output(four_cell_demo)}], ambiguous_query)
    assert any("fixed_four_source_cells" in reason for reason in ambiguous)

    teaching_demo = gen.generate(99, 2, source_cells=7, n_markers=5)
    assert gen.lesson_identifiable([{"input": teaching_demo, "output": rule_output(teaching_demo)}], ambiguous_query) == []


@pytest.mark.parametrize("mutation", ["extra_anchor", "split_source", "missing_branch", "unknown_color", "overlap_stamp"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(71, 4, grid_h=12, grid_w=18, source_cells=5, n_markers=3)
    changed = deepcopy(grid)
    if mutation == "extra_anchor":
        changed[0][0] = 1
    elif mutation == "split_source":
        r, c = color_cells(changed, 2)[0]
        changed[r][c] = 0
        changed[0][0] = 2
    elif mutation == "missing_branch":
        r, c = color_cells(changed, 5)[0]
        changed[r][c] = 0
    elif mutation == "unknown_color":
        changed[0][0] = 9
    elif mutation == "overlap_stamp":
        a = color_cells(changed, 3)[0]
        b = color_cells(changed, 4)[0]
        changed[a[0]][a[1]] = 0
        changed[b[0]][b[1]] = 3
    assert gen.self_check(changed)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 16 for _ in range(10)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output([sys.executable, "-B", "-c", script, str(HOME / "workspace")], env=env, text=True))
    assert results[0] == results[1]


def test_real_racket_reference_matches_independent_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, i, source_cells=3 + i % 5, n_markers=3 + i % 3) for i in range(24)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
