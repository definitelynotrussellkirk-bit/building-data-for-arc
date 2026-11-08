"""Task-local red/green regressions for the contact-degree curriculum."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    analyze,
    authority_output,
    canonical_pairs,
    color_three_output,
    fixed_degree_two_output,
    lesson_pairs,
    load_generator,
    maximum_degree_output,
    observed,
    profile_name,
    unchanged_after_calls,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_metadata_rule_pin_and_literal_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == "1f9fef86a482"
    assert gen.RULE_HASH == "dfe6e5f597b6"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "scene_profile", "header_style"}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_owned_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert authority_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_has_three_answer_identifying_profiles(band):
    seen = []
    for index in range(6):
        grid = gen.generate(91, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == authority_output(grid)
        seen.append(profile_name(grid))
    assert seen == ["chain", "all_degrees", "star", "all_degrees", "chain", "all_degrees"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_demo_window_is_identifiable(band):
    for seed in range(6):
        for start in range(6):
            pairs = lesson_pairs(gen, seed=seed, start=start, band=band or "medium")
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_pair_in_a_four_sample_block_can_be_the_query(band):
    for seed in range(8):
        for start in range(8):
            pairs = lesson_pairs(gen, seed=seed, start=start, band=band or "medium")
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_pixel_observable_in_every_band(band):
    for profile in gen.SCENE_PROFILES:
        for style in gen.HEADER_STYLES:
            controls = {
                "grid_h": 15,
                "grid_w": 17,
                "scene_profile": profile,
                "header_style": style,
            }
            grid = gen.generate(17, 23, difficulty=band, **controls)
            assert observed(grid) == controls
            assert gen.observe_overrides(grid) == controls
            assert gen.self_check(grid, meta=controls) == []


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown", 1),
        ("grid_h", 7),
        ("grid_h", 16),
        ("grid_w", 10),
        ("grid_w", 18),
        ("grid_h", True),
        ("grid_w", 12.5),
        ("scene_profile", "hub"),
        ("header_style", "random"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_all_degrees_profile_refutes_maximum_and_fixed_shortcuts():
    for target_index in (2, 5):
        grid = gen.generate(123, target_index, scene_profile="all_degrees")
        facts = analyze(grid)
        assert set(facts["degrees"]) == {0, 1, 2, 3, 4}
        assert max(facts["degrees"]) > facts["target_degree"]
        expected = authority_output(grid)
        assert maximum_degree_output(grid) != expected
        if facts["target_degree"] == 3:
            assert fixed_degree_two_output(grid) != expected
        assert gen.SEMANTIC_WITNESSES["higher_degree_distractor"](grid)
        assert gen.SEMANTIC_RIVALS["maximum_degree"](grid) == maximum_degree_output(grid)


def test_canonical_maximum_degree_shortcut_has_generated_counterexample():
    assert all(maximum_degree_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = gen.generate(712, 2, scene_profile="all_degrees")
    assert gen.CANONICAL_SHORTCUTS["maximum_degree"](witness) != authority_output(witness)
    assert "maximum_degree" in gen.WITNESS_RIVALS["higher_degree_distractor"]


def test_target_color_and_header_degree_are_not_lookup_shortcuts():
    grids = [gen.generate(551, index) for index in range(12)]
    assert {analyze(grid)["target_degree"] for grid in grids} == {2, 3}
    assert any(color_three_output(grid) != authority_output(grid) for grid in grids)
    assert any(fixed_degree_two_output(grid) != authority_output(grid) for grid in grids)
    assert set(gen.LESSON_COMPETITORS) >= {"maximum_degree", "fixed_degree_two", "color_three"}


def test_self_check_rejects_structural_impostors_and_mutations():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)]]
    for grid in malformed:
        assert gen.self_check(grid)

    base = gen.generate(314, 2, scene_profile="all_degrees")
    mutations = []

    no_header = deepcopy(base)
    no_header[0] = [0] * len(no_header[0])
    mutations.append(no_header)

    body_header_color = deepcopy(base)
    body_header_color[2][0] = 1
    mutations.append(body_header_color)

    output_color_in_input = deepcopy(base)
    output_color_in_input[2][0] = 8
    mutations.append(output_color_in_input)

    no_separator = deepcopy(base)
    no_separator[1][0] = 2
    mutations.append(no_separator)

    blank_body = deepcopy(base)
    for row in range(1, len(blank_body)):
        blank_body[row] = [0] * len(blank_body[row])
    mutations.append(blank_body)

    for mutation in mutations:
        assert gen.self_check(mutation)


def test_determinism_fresh_returns_and_input_purity():
    state = random.getstate()
    first = gen.generate(2026, 8, difficulty="hard")
    assert random.getstate() == state
    snapshot = deepcopy(first)
    second = gen.generate(2026, 8, difficulty="hard")
    assert first == second == snapshot
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert unchanged_after_calls(gen, first)
    assert random.getstate() == state
    first[0][0] = 9
    assert gen.generate(2026, 8, difficulty="hard") == snapshot
