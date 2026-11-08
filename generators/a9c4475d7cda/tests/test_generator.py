"""Regression tests for the threshold-count curriculum of task a9c4475d7cda."""
from __future__ import annotations

import importlib.util
import json
import os
from collections import Counter
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
TASK = "a9c4475d7cda"
PROFILES = {"canonical_bridge", "balanced", "sparse", "dense"}
EXPECTED_HISTOGRAMS = {
    "canonical_bridge": Counter({1: 5, 2: 3, 3: 1}),
    "balanced": Counter({2: 3, 0: 2, 1: 2, 3: 2}),
    "sparse": Counter({0: 4, 1: 3, 2: 1, 3: 1}),
    "dense": Counter({3: 4, 2: 3, 0: 1, 1: 1}),
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_a9c4475d7cda", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_pairs():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                test = row.get("test", [])
                return row["train"] + (test if isinstance(test, list) else [test])
    raise AssertionError("canonical task row is missing")


def _panel_counts(grid):
    height, width = len(grid), len(grid[0])
    separator_rows = [r for r in range(height) if all(value == 8 for value in grid[r])]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 8 for r in range(height))
    ]
    assert len(separator_rows) == len(separator_cols) == 2
    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            sum(
                grid[r][c] == 6
                for r in range(row_start, row_end)
                for c in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]


def _threshold_output(grid, predicate):
    return [[int(predicate(count)) for count in row] for row in _panel_counts(grid)]


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "8cfb5cf9c2c4"


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_accepts_canonical_inputs_and_matches_all_authoritative_outputs(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", sorted(PROFILES))
def test_exact_axes_are_honored_and_observable_in_every_band(band, profile):
    grid = GEN.generate(
        1701,
        19,
        difficulty=band,
        grid_h=9,
        grid_w=17,
        count_profile=profile,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 9,
        "grid_w": 17,
        "count_profile": profile,
    }
    assert Counter(value for row in _panel_counts(grid) for value in row) == EXPECTED_HISTOGRAMS[profile]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 8},
        {"grid_h": 18},
        {"grid_w": True},
        {"grid_w": "11"},
        {"count_profile": "unknown"},
        {"count_profile": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_semantically_complete(band):
    seen_profiles = set()
    seen_shapes = set()
    for index in range(96):
        grid = GEN.generate(4100 + index, index * 7, difficulty=band)
        assert grid == GEN.generate(4100 + index, index * 7, difficulty=band)
        assert GEN.self_check(grid) == []
        counts = [value for row in _panel_counts(grid) for value in row]
        assert {1, 2, 3} <= set(counts)
        observed = GEN.observe_overrides(grid)
        seen_profiles.add(observed["count_profile"])
        seen_shapes.add((len(grid), len(grid[0])))
    assert seen_profiles == PROFILES
    assert (11, 11) in seen_shapes
    assert len(seen_shapes) >= 12


def test_exactly_two_is_a_real_canonical_shortcut_and_generated_counterexample():
    assert all(
        _threshold_output(pair["input"], lambda count: count == 2) == pair["output"]
        for pair in _canonical_pairs()
    )
    grid = GEN.generate(811, 3, grid_h=11, grid_w=11, count_profile="canonical_bridge")
    intended = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["exactly_two"](grid)
    assert intended == _threshold_output(grid, lambda count: count >= 2)
    assert rival == _threshold_output(grid, lambda count: count == 2)
    differing = [
        (r, c)
        for r in range(3)
        for c in range(3)
        if intended[r][c] != rival[r][c]
    ]
    counts = _panel_counts(grid)
    assert differing
    assert all(counts[r][c] == 3 for r, c in differing)
    assert GEN.SEMANTIC_WITNESSES["count_three"](grid)
    assert GEN.CANONICAL_SHORTCUTS["exactly_two"](grid) == rival
    assert GEN.LESSON_COMPETITORS["exactly_two"](grid) == rival


def test_nonempty_rival_is_also_refuted_by_every_generated_profile():
    for profile in PROFILES:
        grid = GEN.generate(902, 4, count_profile=profile)
        rival = GEN.SEMANTIC_RIVALS["nonempty"](grid)
        intended = GEN.rule_mirror(grid)
        counts = _panel_counts(grid)
        differing = [
            (r, c)
            for r in range(3)
            for c in range(3)
            if rival[r][c] != intended[r][c]
        ]
        assert differing
        assert all(counts[r][c] == 1 for r, c in differing)


@pytest.mark.parametrize("mutation", ["erase_divider", "stray_eight", "unknown_color", "erase_sixes"])
def test_self_check_rejects_structure_destroying_mutations(mutation):
    grid = GEN.generate(73, 5, grid_h=11, grid_w=11, count_profile="balanced")
    if mutation == "erase_divider":
        separator_row = next(r for r, row in enumerate(grid) if all(value == 8 for value in row))
        grid[separator_row][0] = 0
    elif mutation == "stray_eight":
        position = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0
        )
        grid[position[0]][position[1]] = 8
    elif mutation == "unknown_color":
        position = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0
        )
        grid[position[0]][position[1]] = 4
    else:
        for row in grid:
            for c, value in enumerate(row):
                if value == 6:
                    row[c] = 0
    assert GEN.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]])
def test_malformed_grid_returns_diagnostics_instead_of_throwing(grid):
    assert GEN.self_check(grid)
