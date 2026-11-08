"""Task-local regression tests for 99f58784e7a0."""
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
    LAYOUT_SPANS,
    canonical_pairs,
    chamber_analysis,
    connected_nonwall_components,
    distinct_colors_only_rival,
    intended_output,
    load_generator,
    observed,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_canonical_authority():
    assert gen.RULE_HASH == "5f0096488100"


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("layout_profile,scale", sorted(LAYOUT_SPANS))
@pytest.mark.parametrize("color_pattern", ["distinct", "reused"])
def test_every_exact_axis_combination_is_constructive_and_observable(
    band, layout_profile, scale, color_pattern
):
    requested = {
        "layout_profile": layout_profile,
        "scale": scale,
        "color_pattern": color_pattern,
    }
    grid = gen.generate(173, 29, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert intended_output(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("layout_profile", "diagonal"),
        ("layout_profile", 1),
        ("scale", "huge"),
        ("scale", 0),
        ("color_pattern", "rainbow"),
        ("color_pattern", True),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_invalid_difficulty_fails_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_noninteger_seed_fails_loudly(seed):
    with pytest.raises(ValueError):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_fails_loudly(sample_index):
    with pytest.raises(ValueError):
        gen.generate(0, sample_index)
    with pytest.raises(ValueError):
        gen.schedule_profile(0, sample_index)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_covers_all_layouts_scales_and_color_patterns(band):
    stats = [observed(gen.generate(700 + i, i, difficulty=band)) for i in range(16)]
    assert {item["layout_profile"] for item in stats} == {
        "vertical_unequal",
        "vertical_equal",
        "horizontal_three",
        "grid_2x2",
    }
    assert {item["scale"] for item in stats} == {"canonical", "expanded"}
    assert {item["color_pattern"] for item in stats} == {"distinct", "reused"}
    # Any three consecutive demos contain a reused-color counterexample.
    for start in range(16):
        window = [stats[(start + offset) % len(stats)] for offset in range(3)]
        assert any(item["color_pattern"] == "reused" for item in window)


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(99173)
    state = random.getstate()
    first = gen.generate(19, 31, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


@pytest.mark.parametrize(
    "mutation",
    [
        "blank",
        "ragged",
        "unknown_color",
        "broken_border",
        "stray_wall",
        "missing_seed",
        "multiple_seeds",
    ],
)
def test_self_check_rejects_structural_impostors(mutation):
    grid = gen.generate(
        41,
        7,
        layout_profile="grid_2x2",
        scale="canonical",
        color_pattern="distinct",
    )
    analysis = chamber_analysis(grid)
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "unknown_color":
        grid[1][1] = 10
    elif mutation == "broken_border":
        grid[0][1] = 0
    elif mutation == "stray_wall":
        chamber = analysis["chambers"][0]
        r, c = next(cell for cell in chamber["cells"] if grid[cell[0]][cell[1]] == 0)
        grid[r][c] = 8
    elif mutation == "missing_seed":
        r, c, _ = analysis["chambers"][0]["seed"]
        grid[r][c] = 0
    elif mutation == "multiple_seeds":
        chamber = analysis["chambers"][0]
        r, c = next(cell for cell in chamber["cells"] if grid[cell[0]][cell[1]] == 0)
        grid[r][c] = 7
    assert gen.self_check(grid), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 4 for _ in range(4)]])
def test_self_check_reports_malformed_inputs_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_rule_mirror_is_pure_and_matches_connected_component_formulation():
    grid = gen.generate(93, 11, color_pattern="reused", scale="expanded")
    original = deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output == intended_output(grid)
    analysis = chamber_analysis(grid)
    components = connected_nonwall_components(grid)
    assert len(components) == len(analysis["chambers"])
    for component in components:
        colors = {grid[r][c] for r, c in component} - {0}
        assert len(colors) == 1
        color = next(iter(colors))
        assert all(output[r][c] == color for r, c in component)


def test_declared_shortcut_fits_all_canonical_pairs_but_reused_colors_refute_it():
    rival = gen.SEMANTIC_RIVALS["distinct_colors_only"]
    assert gen.CANONICAL_SHORTCUTS["distinct_colors_only"] is rival
    assert gen.LESSON_COMPETITORS["distinct_colors_only"] is rival
    for pair in canonical_pairs():
        assert distinct_colors_only_rival(pair["input"]) == pair["output"]
        assert rival(pair["input"]) == pair["output"]

    witness = gen.generate(
        512,
        3,
        layout_profile="grid_2x2",
        scale="canonical",
        color_pattern="reused",
    )
    assert gen.SEMANTIC_WITNESSES["reused_seed_color"](witness)
    assert rival(witness) == distinct_colors_only_rival(witness)
    assert rival(witness) != intended_output(witness)


@pytest.mark.parametrize(
    "query_pattern,expect_ambiguity",
    [("distinct", False), ("reused", True)],
)
def test_lesson_identifiable_only_flags_competitor_when_query_answer_changes(
    query_pattern, expect_ambiguity
):
    demos = []
    for index, layout_profile in enumerate(
        ("vertical_unequal", "horizontal_three", "grid_2x2")
    ):
        grid = gen.generate(
            2000 + index,
            index,
            layout_profile=layout_profile,
            scale="canonical",
            color_pattern="distinct",
        )
        output = intended_output(grid)
        assert distinct_colors_only_rival(grid) == output
        demos.append({"input": grid, "output": output})

    query_grid = gen.generate(
        2100,
        7,
        layout_profile="grid_2x2",
        scale="expanded",
        color_pattern=query_pattern,
    )
    query_output = intended_output(query_grid)
    assert (distinct_colors_only_rival(query_grid) != query_output) is expect_ambiguity

    reasons = gen.lesson_identifiable(
        demos,
        {"input": query_grid, "output": query_output},
    )
    competitor_reasons = [reason for reason in reasons if "distinct_colors_only" in reason]
    assert bool(competitor_reasons) is expect_ambiguity
    assert reasons == competitor_reasons


def test_every_three_demo_schedule_window_identifies_declared_rival():
    assert gen.EXAMPLES_NEEDED == 3
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(3000 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": intended_output(grid)})
            query_grid = gen.generate(9000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": intended_output(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_difficulty_bands_shift_the_default_curriculum():
    for index in range(8):
        profiles = {
            tuple(sorted(observed(gen.generate(12000 + index, index, difficulty=band)).items()))
            for band in ("easy", "medium", "hard")
        }
        assert len(profiles) == 3


def test_all_cyclic_query_rotations_of_a_four_sample_window_identify_the_rival():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            examples = []
            for offset in range(4):
                grid = gen.generate(16000 + start, start + offset, difficulty=band)
                examples.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                query = examples[query_index]
                demos = examples[query_index + 1 :] + examples[:query_index]
                assert len(demos) == 3
                assert gen.lesson_identifiable(demos, query) == []
