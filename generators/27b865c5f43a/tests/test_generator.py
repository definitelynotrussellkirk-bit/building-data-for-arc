"""Task-local regression and semantic curriculum tests for 27b865c5f43a."""
from __future__ import annotations

from copy import deepcopy
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    color_order_conflict,
    color_sorted_output,
    load_generator,
    observed,
    retained_degenerate_inputs,
    row_order_conflict,
    row_sorted_output,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
PALETTES = ("ascending", "mixed", "permuted", "descending")
SHAPE_SETS = ("sparse", "mixed", "dense")
ROW_PATTERNS = ("aligned", "reverse", "valley", "peak")
EXPECTED_AXES = {"grid_h", "grid_w", "palette_kind", "shape_set", "row_pattern"}
CANONICAL_PROFILES = {(8, 17, 4), (8, 18, 4), (9, 18, 4), (9, 20, 4)}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_authority_pin_and_honest_public_contract():
    assert gen.RULE_HASH == "de4d9d03f710"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.SEMANTIC_RIVALS) == {"color_sort", "row_sort"}
    assert set(gen.CANONICAL_SHORTCUTS) == {"color_sort", "row_sort"}
    assert set(gen.LESSON_COMPETITORS) == {"color_sort", "row_sort"}
    assert gen.WITNESS_RIVALS == {
        "color_order_conflict": ("color_sort",),
        "row_order_conflict": ("row_sort",),
    }


@pytest.mark.parametrize(
    "canonical",
    canonical_pairs(),
    ids=lambda item: f"{item['split']}-{item['pair_index']}",
)
def test_all_canonical_inputs_are_accepted_and_oracle_matches(canonical):
    original = deepcopy(canonical["input"])
    assert gen.self_check(canonical["input"]) == []
    assert gen.strict_canonical_like(canonical["input"]) == []
    assert rule_output(canonical["input"]) == canonical["output"]
    assert gen.rule_mirror(canonical["input"]) == canonical["output"]
    assert canonical["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_every_public_override_combination_is_exact_observable_and_lawful(band):
    index = 0
    for grid_h, grid_w, palette, shape_set, row_pattern in itertools.product(
        (8, 9), range(17, 21), PALETTES, SHAPE_SETS, ROW_PATTERNS
    ):
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "palette_kind": palette,
            "shape_set": shape_set,
            "row_pattern": row_pattern,
        }
        grid = gen.generate(50_000 + index, index, difficulty=band, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)
        assert grid == gen.generate(50_000 + index, index, difficulty=band, **requested)
        index += 1


@pytest.mark.parametrize(
    "overrides",
    (
        {"typo_axis": 1},
        {"grid_h": 7}, {"grid_h": 10}, {"grid_w": 16}, {"grid_w": 21},
        {"grid_h": True}, {"grid_h": 8.0}, {"grid_w": "18"},
        {"palette_kind": "default"}, {"palette_kind": 1},
        {"shape_set": "all_same"}, {"shape_set": 2},
        {"row_pattern": "random"}, {"row_pattern": None.__class__},
    ),
)
def test_invalid_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True, 2))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed,sample_index", ((True, 0), (1.5, 0), (1, True), (1, -1)))
def test_invalid_seed_or_sample_index_is_rejected(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_retained_degenerate_counterexamples_are_rejected_even_with_metadata():
    for name, grid in retained_degenerate_inputs().items():
        assert gen.self_check(grid), name
        assert gen.self_check(grid, meta={"texture": name}), name


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_has_exact_canonical_profiles_and_all_semantic_branches(band):
    profiles = set()
    palettes = set()
    shape_sets = set()
    row_patterns = set()
    unique = set()
    for index in range(48):
        grid = gen.generate(9_100 + index, index, difficulty=band)
        assert grid == gen.generate(9_100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        state = observed(grid)
        profiles.add(profile(grid))
        palettes.add(state["palette_kind"])
        shape_sets.add(state["shape_set"])
        row_patterns.add(state["row_pattern"])
        unique.add(tuple(tuple(row) for row in grid))
    assert profiles == CANONICAL_PROFILES
    assert palettes == set(PALETTES)
    assert shape_sets == set(SHAPE_SETS)
    assert row_patterns == set(ROW_PATTERNS)
    assert len(unique) >= 40


def test_canonical_fitting_shortcuts_are_real_and_generated_witnesses_refute_them():
    canonical = canonical_pairs()
    assert all(color_sorted_output(pair["input"]) == pair["output"] for pair in canonical)
    assert all(row_sorted_output(pair["input"]) == pair["output"] for pair in canonical)

    color_witness = gen.generate(
        17, 1, grid_h=8, grid_w=18, palette_kind="permuted",
        shape_set="mixed", row_pattern="aligned",
    )
    row_witness = gen.generate(
        19, 2, grid_h=9, grid_w=20, palette_kind="ascending",
        shape_set="dense", row_pattern="reverse",
    )
    assert color_order_conflict(color_witness)
    assert gen.SEMANTIC_WITNESSES["color_order_conflict"](color_witness)
    assert gen.rule_mirror(color_witness) != gen.SEMANTIC_RIVALS["color_sort"](color_witness)
    assert row_order_conflict(row_witness)
    assert gen.SEMANTIC_WITNESSES["row_order_conflict"](row_witness)
    assert gen.rule_mirror(row_witness) != gen.SEMANTIC_RIVALS["row_sort"](row_witness)


@pytest.mark.parametrize("band", BANDS)
def test_each_five_example_schedule_survives_every_query_rotation(band):
    # The downstream census holds each of five materialized pairs out once.
    # Every remaining four-demo set must refute both canonical-fitting rivals.
    for start in range(24):
        pairs = []
        for offset in range(5):
            index = start + offset
            grid = gen.generate(70_000 + index, index, difficulty=band)
            pairs.append({"input": grid, "output": rule_output(grid)})
        for held_out in range(5):
            demos = [pair for i, pair in enumerate(pairs) if i != held_out]
            assert any(color_sorted_output(pair["input"]) != pair["output"] for pair in demos)
            assert any(row_sorted_output(pair["input"]) != pair["output"] for pair in demos)
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []
