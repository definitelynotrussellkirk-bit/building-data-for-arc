"""Regression tests for the reviewed 1e07c169ac61 generator."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    PROFILES,
    TASK_ID,
    ambiguity_records,
    anchor,
    center_pivot,
    first_color_only,
    largest_component_only,
    load_generator,
    malformed_grids,
    observed,
    rotation_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_is_pinned_to_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "b7275e98009a"


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_canonical_inputs_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert rotation_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 6,
            "grid_w": 10,
            "foreground_size": 3,
            "profile": "mono_connected",
        },
        {
            "grid_h": 10,
            "grid_w": 6,
            "foreground_size": 8,
            "profile": "multicolor_disconnected",
        },
        {
            "grid_h": 7,
            "grid_w": 7,
            "foreground_size": 6,
            "profile": "multicolor_connected",
        },
    ],
)
def test_exact_overrides_are_constructive_and_observable_in_every_band(band, overrides):
    grid = gen.generate(1701, 29, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 5},
        {"grid_h": 11},
        {"grid_w": True},
        {"foreground_size": 2},
        {"foreground_size": 9},
        {"foreground_size": 3.0},
        {"profile": "upper_left_only"},
        {"profile": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")


def test_default_distribution_is_deterministic_and_covers_teaching_profiles():
    profiles: set[str] = set()
    anchors: set[tuple[int, int, int, int]] = set()
    sizes: set[tuple[int, int]] = set()
    quadrants: set[tuple[bool, bool, bool, bool]] = set()
    unique: set[tuple[tuple[int, ...], ...]] = set()
    for index in range(256):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(9100 + index, index, difficulty=band)
        assert grid == gen.generate(9100 + index, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        stats = observed(grid)
        profiles.add(stats["profile"])
        sizes.add((stats["grid_h"], stats["grid_w"]))
        ar, ac = anchor(grid)
        anchors.add((len(grid), len(grid[0]), ar, ac))
        assert (ar, ac) != (len(grid) // 2, len(grid[0]) // 2)
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value not in (0, 9)
        ]
        quadrants.add(
            (
                any(r < ar and c < ac for r, c in cells),
                any(r < ar and c > ac for r, c in cells),
                any(r > ar and c < ac for r, c in cells),
                any(r > ar and c > ac for r, c in cells),
            )
        )
        unique.add(tuple(tuple(row) for row in grid))
    assert profiles == set(PROFILES)
    assert {(6, 6), (7, 7)} <= sizes
    assert len(sizes) >= 10
    assert len(anchors) >= 40
    assert any(sum(flags) >= 2 for flags in quadrants)
    assert len(unique) >= 250


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_contains_canonical_exact_profiles(band):
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for index in range(20)
        for grid in [gen.generate(3000 + index, index, difficulty=band)]
    }
    assert profiles & {(6, 6, 3), (7, 7, 3)}


def test_canonical_shortcuts_fit_examples_but_generated_profiles_refute_them():
    assert all(first_color_only(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(largest_component_only(pair["input"]) == pair["output"] for pair in PAIRS)

    by_profile = {
        profile: gen.generate(700 + i, i, profile=profile)
        for i, profile in enumerate(PROFILES)
    }
    for grid in by_profile.values():
        assert center_pivot(grid) != rotation_output(grid)
    for profile in ("multicolor_connected", "multicolor_disconnected"):
        assert first_color_only(by_profile[profile]) != rotation_output(by_profile[profile])
    for profile in ("mono_disconnected", "multicolor_disconnected"):
        assert largest_component_only(by_profile[profile]) != rotation_output(by_profile[profile])


def test_semantic_contract_names_real_witnesses_and_rivals():
    for index, profile in enumerate(PROFILES):
        grid = gen.generate(4400 + index, index, profile=profile)
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["off_center_anchor"](grid)
        assert gen.SEMANTIC_RIVALS["center_pivot"](grid) == center_pivot(grid)
        assert gen.SEMANTIC_RIVALS["center_pivot"](grid) != rotation_output(grid)
        if profile.startswith("multicolor"):
            assert gen.SEMANTIC_WITNESSES["multicolor"](grid)
            assert gen.SEMANTIC_RIVALS["first_color_only"](grid) == first_color_only(grid)
        if profile.endswith("disconnected"):
            assert gen.SEMANTIC_WITNESSES["disconnected"](grid)
            assert gen.SEMANTIC_RIVALS["largest_component_only"](grid) == largest_component_only(grid)


def test_every_cyclic_window_and_query_rotation_refutes_declared_competitors():
    period = len(gen.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for seed in (61_001, 61_002):
            for start in range(period * 2):
                grids = [
                    gen.generate(seed, start + offset, difficulty=band)
                    for offset in range(gen.EXAMPLES_NEEDED + 1)
                ]
                pairs = [
                    {"input": grid, "output": rotation_output(grid)}
                    for grid in grids
                ]
                assert ambiguity_records(pairs, gen.LESSON_COMPETITORS) == []


@pytest.mark.parametrize("grid", malformed_grids())
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)
