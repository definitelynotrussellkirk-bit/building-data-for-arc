"""Regression tests for the reviewed dfda42e49ff5 generator."""
from __future__ import annotations

import os
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    COUNTEREXAMPLE,
    GLOBAL_RIGHT_COUNTEREXAMPLE,
    RIVALS,
    TASK_ID,
    analyze,
    component_global_right_span,
    freeze,
    intended_output,
    largest_component_only,
    load_generator,
    per_color_row_span,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
BANDS = (None, "easy", "medium", "hard")
RICH_PROFILES = ("same_color_pair", "same_color_trio", "mixed_cluster")


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "2241d1285117"


@pytest.mark.parametrize("pair", PAIRS, ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_named_canonical_shortcuts_really_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "per_color_row_span",
        "largest_component_only",
        "component_global_right_span",
    }
    for pair in PAIRS:
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "profile,expected",
    [
        ("canonical_single", (1, 1)),
        ("same_color_pair", (2, 1)),
        ("same_color_trio", (3, 1)),
        ("mixed_cluster", (3, 2)),
    ],
)
def test_scene_profile_override_is_exact_observable_and_constructive(band, profile, expected):
    grid = gen.generate(1801, 13, difficulty=band, scene_profile=profile)
    stats = analyze(grid)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": {"scene_profile": profile}}) == []
    assert (stats["component_count"], stats["color_count"]) == expected
    assert gen.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"scene_profile": "one_object"},
        {"scene_profile": 1},
        {"scene_profile": True},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")


def test_default_schedule_covers_all_profiles_in_every_four_samples():
    profiles = tuple(gen.SCHEDULE_PROFILES)
    assert len(profiles) == 4
    for start in range(12):
        observed = {
            gen.observe_overrides(gen.generate(700, start + offset))["scene_profile"]
            for offset in range(4)
        }
        assert observed == set(profiles)


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_is_deterministic_lawful_and_varied(band):
    unique = set()
    shapes = set()
    sizes = set()
    gaps = set()
    before = random.getstate()
    for index in range(128):
        seed = 3000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        stats = analyze(grid)
        unique.add(freeze(grid))
        shapes.update(stats["normalized_shapes"])
        sizes.update(stats["component_sizes"])
        gaps.add(stats["max_gap"])
    assert random.getstate() == before
    assert len(unique) >= 120
    assert len(shapes) >= 12
    assert max(sizes) >= 10
    assert max(gaps) >= 3


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_each_band_has_exact_canonical_profile_support_in_twenty_draws(band):
    profiles = []
    for index in range(20):
        grid = gen.generate(9000 + index, index, difficulty=band)
        stats = analyze(grid)
        profiles.append((stats["grid_h"], stats["grid_w"], stats["component_count"], stats["color_count"]))
    assert any(height == 5 and width in (7, 8, 9) and components == colors == 1
               for height, width, components, colors in profiles)


@pytest.mark.parametrize("profile", RICH_PROFILES)
def test_every_rich_profile_refutes_every_declared_competitor(profile):
    for index in range(24):
        grid = gen.generate(11_000 + index, index, difficulty="hard", scene_profile=profile)
        expected = intended_output(grid)
        assert gen.rule_mirror(grid) == expected
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != expected, (profile, index, name)


def test_exact_same_color_counterexample_separates_object_rule_from_color_shortcut():
    expected = intended_output(COUNTEREXAMPLE)
    rival = per_color_row_span(COUNTEREXAMPLE)
    assert gen.self_check(COUNTEREXAMPLE) == []
    assert gen.rule_mirror(COUNTEREXAMPLE) == expected
    assert expected != rival
    assert expected[1] == [2, 2, 2, 2, 0, 0, 2, 2, 2, 2, 0]
    assert rival[1] == [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0]
    generated = gen.generate(13, 1, scene_profile="same_color_pair")
    assert intended_output(generated) != per_color_row_span(generated)



def test_global_right_shortcut_has_an_exact_canonical_fitting_counterexample():
    expected = intended_output(GLOBAL_RIGHT_COUNTEREXAMPLE)
    rival = component_global_right_span(GLOBAL_RIGHT_COUNTEREXAMPLE)
    assert gen.self_check(GLOBAL_RIGHT_COUNTEREXAMPLE) == []
    assert expected != rival
    assert expected[1] == [0, 2, 2, 2, 2, 0, 0, 0]
    assert rival[1] == [0, 2, 2, 2, 2, 2, 2, 0]


@pytest.mark.parametrize("profile", RICH_PROFILES)
def test_every_rich_profile_refutes_global_right_shortcut(profile):
    for index in range(24):
        grid = gen.generate(11_000 + index, index, difficulty="hard", scene_profile=profile)
        assert component_global_right_span(grid) != intended_output(grid), (profile, index)

def test_largest_only_shortcut_is_refuted_by_generated_multi_object_scene():
    grid = gen.generate(19, 2, scene_profile="mixed_cluster")
    assert intended_output(grid) != largest_component_only(grid)


def test_semantic_contract_names_real_witnesses_and_independent_rivals():
    grid = gen.generate(73, 3, scene_profile="mixed_cluster")
    assert gen.SEMANTIC_WITNESSES["same_color_disconnected_row_overlap"](grid)
    assert gen.SEMANTIC_WITNESSES["multiple_changed_objects"](grid)
    assert gen.SEMANTIC_WITNESSES["row_bounds_not_component_bbox"](grid)
    assert gen.SEMANTIC_WITNESSES["row_right_bound_not_component_right"](grid)
    assert gen.SEMANTIC_WITNESSES["wide_row_gap"](grid)
    for name, independent in RIVALS.items():
        assert gen.SEMANTIC_RIVALS[name](grid) == independent(grid)
        assert gen.SEMANTIC_RIVALS[name](grid) != intended_output(grid)


def test_every_four_pair_window_is_identifiable_under_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for offset in range(4):
                grid = gen.generate(21_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0, 0], [0, 0]],
        [[1, 1], [1, 1]],
    ],
)
def test_malformed_or_rule_hiding_inputs_return_diagnostics(grid):
    assert gen.self_check(grid)


def test_retained_counterexample_fixture_matches_the_exercised_case():
    import json

    fixture = HOME / "counterexamples" / "per_color_row_span_input.json"
    assert json.loads(fixture.read_text()) == COUNTEREXAMPLE


def test_retained_global_right_counterexample_fixture_matches_exercised_case():
    import json

    fixture = HOME / "counterexamples" / "component_global_right_span_input.json"
    assert json.loads(fixture.read_text()) == GLOBAL_RIGHT_COUNTEREXAMPLE
