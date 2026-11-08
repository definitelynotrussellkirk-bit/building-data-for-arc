"""Regression and semantic-contract tests for 506e262f9354."""
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
    decoy_counterexample,
    explicit_counterexample,
    features,
    intended_output,
    line_length_rival,
    load_generator,
    observed,
    preserve_decoys_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(5, 7, 4), (7, 8, 5), (9, 9, 7)}


def _pair(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def test_rule_pin_and_contract_surface():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "d19e95f77d58"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert tuple(gen.SCHEDULE_PROFILES) == ("canonical_core", "teaching")
    assert set(gen.AXES) == {
        "grid_h", "grid_w", "n_sevens", "column_position", "decoy_count"
    }


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    pairs = canonical_pairs()
    assert len(pairs) >= 3
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("position", ["left", "center", "right", "interior"])
@pytest.mark.parametrize("decoys", [0, 4])
def test_exact_controls_are_observable_in_every_band(band, position, decoys):
    requested = {
        "grid_h": 9,
        "grid_w": 11,
        "n_sevens": 7,
        "column_position": position,
        "decoy_count": decoys,
    }
    grid = gen.generate(177, 8, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert observed(grid) == requested


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_full_height_source_override_is_supported_even_on_teaching_indices(band):
    requested = {
        "grid_h": 5,
        "grid_w": 7,
        "n_sevens": 5,
        "column_position": "center",
        "decoy_count": 4,
    }
    grid = gen.generate(177, 1, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert observed(grid) == requested
    assert features(grid)["shifted_column"] is False
    assert features(grid)["erasable_decoy"] is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 4}, {"grid_h": 17}, {"grid_h": True},
        {"grid_w": 6}, {"grid_w": 19}, {"grid_w": 9.0},
        {"n_sevens": 1}, {"n_sevens": 8}, {"n_sevens": "4"},
        {"column_position": "random"}, {"column_position": 0},
        {"decoy_count": -1}, {"decoy_count": 5}, {"decoy_count": False},
        {"grid_h": 5, "n_sevens": 7},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_default_schedule_visits_one_core_and_two_teaching_profiles_per_three_indices():
    for start in range(30):
        profiles = [gen.schedule_profile(91, start + offset, "hard") for offset in range(3)]
        assert profiles.count("canonical_core") == 1
        assert profiles.count("teaching") == 2


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_profile_supported(band):
    profile_hits = 0
    distinct = set()
    for index in range(60):
        grid = gen.generate(7000 + index, index, difficulty=band)
        assert grid == gen.generate(7000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        facts = features(grid)
        if gen.schedule_profile(7000 + index, index, band) == "canonical_core":
            assert facts["canonical_like"]
        else:
            assert facts["shifted_column"]
            assert facts["erasable_decoy"]
        obs = observed(grid)
        profile_hits += (obs["grid_h"], obs["grid_w"], obs["n_sevens"]) in CANONICAL_PROFILES
        distinct.add(tuple(tuple(row) for row in grid))
    assert profile_hits >= 15
    assert len(distinct) >= 48


def test_line_length_shortcut_fits_every_canonical_pair_but_exact_witness_refutes_it():
    assert all(line_length_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = explicit_counterexample()
    assert gen.self_check(grid) == []
    assert features(grid)["shifted_column"]
    assert line_length_rival(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["line_length_triangle"](grid) == line_length_rival(grid)


def test_preserve_decoys_shortcut_fits_canonical_but_generated_witness_refutes_it():
    assert all(preserve_decoys_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = decoy_counterexample()
    assert gen.self_check(grid) == []
    assert features(grid)["erasable_decoy"]
    assert preserve_decoys_rival(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["preserve_decoys"](grid) == preserve_decoys_rival(grid)


def test_every_four_pair_rotation_is_identifiable_against_declared_shortcuts():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(gen.generate(9000 + start, start + offset, difficulty=band))
                     for offset in range(4)]
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for rival in gen.LESSON_COMPETITORS.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_oracles_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(44, 1, difficulty="medium")
    original = deepcopy(grid)
    intended_output(grid)
    line_length_rival(grid)
    preserve_decoys_rival(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


@pytest.mark.parametrize("mutation", ["ragged", "split_column", "gap", "inside_decoy", "too_many_decoys"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        12, 1, grid_h=9, grid_w=11, n_sevens=5,
        column_position="center", decoy_count=1,
    )
    if mutation == "ragged":
        grid[0].pop()
    elif mutation == "split_column":
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
        r, c = cells[0]
        grid[r][c] = 0
        grid[r][c + 1] = 7
    elif mutation == "gap":
        cells = sorted((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7)
        r, c = cells[len(cells) // 2]
        grid[r][c] = 0
    elif mutation == "inside_decoy":
        cells = sorted((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7)
        bottom, col = cells[-1]
        if col + 1 < len(grid[0]):
            grid[bottom - 1][col + 1] = 3
        else:
            grid[bottom - 1][col - 1] = 3
    elif mutation == "too_many_decoys":
        placed = 0
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0:
                    grid[r][c] = 3
                    placed += 1
                    if placed == 6:
                        break
            if placed == 6:
                break
    assert gen.self_check(grid)
