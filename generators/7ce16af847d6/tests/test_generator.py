"""Task-local regression tests for 7ce16af847d6.

The oracle and rivals are independent of generator implementation helpers.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    facts,
    intended_output,
    load_generator,
    profile_of,
    rival_all_blue,
    rival_any_color_exact_3x3,
    rival_blue_bbox_3x3,
    rival_blue_size_nine,
    rival_contains_3x3,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("canonical_mix", "shape_counterexamples", "color_counterexample")
RIVALS = {
    "blue_size_nine": rival_blue_size_nine,
    "blue_bbox_3x3": rival_blue_bbox_3x3,
    "contains_solid_3x3": rival_contains_3x3,
    "any_color_exact_3x3": rival_any_color_exact_3x3,
    "all_blue_components": rival_all_blue,
}


def _pair(seed, index, band):
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": intended_output(grid)}


def test_public_contract_is_pinned_and_minimal():
    assert gen.RULE_HASH == "a7803abc6931"
    assert gen.VERSION == "3.0.0"
    assert tuple(gen.SCENE_PROFILES) == PROFILES
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert gen.SCHEDULE_PERIOD == 3
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}-{pair['pair_index']}",
)
def test_accepts_all_canonical_inputs_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
def test_scene_profile_override_is_exact_and_observable(profile, band):
    grid = gen.generate(17, 9, difficulty=band, scene_profile=profile)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert profile_of(grid) == profile
    assert gen.observe_overrides(grid) == {"scene_profile": profile}
    assert (len(grid), len(grid[0]), len({v for row in grid for v in row})) in {
        (11, 11, 4), (12, 12, 4)
    }


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": "canonical_mix"},
    {"scene_profile": "not-a-profile"},
    {"scene_profile": 1},
    {"scene_profile": None},
])
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError), match="override|scene_profile"):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_consecutive_indices_cover_every_profile(band):
    for seed in range(8):
        for start in range(12):
            observed = {
                gen.schedule_profile(seed, start + offset, band)
                for offset in range(3)
            }
            assert observed == set(PROFILES)


def test_shape_profile_refutes_three_shape_shortcuts():
    grid = gen.generate(31, 0, scene_profile="shape_counterexamples")
    info = facts(grid)
    assert info["blue_hollow_3x3"]
    assert info["blue_nine_cell_non_square"]
    assert info["blue_contains_3x3_but_not_exact"]
    official = intended_output(grid)
    for name in ("blue_bbox_3x3", "blue_size_nine", "contains_solid_3x3"):
        assert gen.SEMANTIC_RIVALS[name](grid) == RIVALS[name](grid)
        assert RIVALS[name](grid) != official


def test_color_profile_refutes_color_agnostic_shortcut():
    grid = gen.generate(37, 0, scene_profile="color_counterexample")
    assert facts(grid)["nonblue_exact_3x3"]
    official = intended_output(grid)
    assert gen.SEMANTIC_RIVALS["any_color_exact_3x3"](grid) == rival_any_color_exact_3x3(grid)
    assert rival_any_color_exact_3x3(grid) != official


def test_canonical_profile_refutes_recolor_every_blue_shortcut():
    grid = gen.generate(41, 0, scene_profile="canonical_mix")
    info = facts(grid)
    assert info["blue_distractors"] >= 2
    assert rival_all_blue(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["all_blue_components"](grid) == rival_all_blue(grid)


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "blue_size_nine", "blue_bbox_3x3", "any_color_exact_3x3"
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        independent = RIVALS[name]
        for pair in canonical_pairs():
            assert rival(pair["input"]) == pair["output"], name
            assert rival(pair["input"]) == independent(pair["input"]), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_scheduled_three_demo_lesson_refutes_all_competitors(band):
    for seed in range(7):
        for start in range(10):
            demos = [_pair(seed, start + offset, band) for offset in range(3)]
            query = _pair(seed, start + 3, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_lesson_identifiability_does_not_read_query_answer():
    demos = [_pair(19, offset, "medium") for offset in range(3)]
    query = _pair(19, 3, "medium")
    clean = gen.lesson_identifiable(demos, {"input": query["input"]})
    poisoned = gen.lesson_identifiable(demos, {"input": query["input"], "output": "DO NOT READ"})
    assert clean == poisoned == []


def test_lesson_identifiability_rejects_bad_or_insufficient_visible_labels():
    demos = [_pair(23, offset, "medium") for offset in range(3)]
    assert gen.lesson_identifiable(demos[:2], {"input": demos[2]["input"]})
    bad = deepcopy(demos)
    bad[0]["output"][0][0] = 9 if bad[0]["output"][0][0] != 9 else 8
    assert gen.lesson_identifiable(bad, {"input": demos[2]["input"]})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_is_deterministic_diverse_and_canonical_scaled(band):
    grids = []
    rows = []
    for index in range(300):
        args = (9000 + index, index * 13 + 7)
        grid = gen.generate(*args, difficulty=band)
        assert grid == gen.generate(*args, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        grids.append(grid)
        rows.append(facts(grid))
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 280
    assert {11, 12} <= {row["height"] for row in rows}
    assert {11, 12} <= {row["width"] for row in rows}
    assert {7, 8} <= {row["components"] for row in rows}
    assert {2, 3} <= {row["targets"] for row in rows}
    assert {tuple(row["palette"]) for row in rows}
    assert all(len(row["palette"]) == 4 for row in rows)
    assert set(PROFILES) == {profile_of(grid) for grid in grids}


def test_rule_and_rivals_are_pure():
    grid = gen.generate(71, 5, scene_profile="shape_counterexamples")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    intended_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


@pytest.mark.parametrize("mutation", [
    "blank", "ragged", "bad_color", "output_color", "remove_target_cell",
    "remove_decoration", "add_third_decor_color", "merge_two_blue_components",
])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(101, 8, scene_profile="canonical_mix")
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "output_color":
        grid[0][0] = 3
    else:
        parts = []
        # Independent component extraction is implicit in facts; locate pixels manually.
        from reference_probe import components
        parts = components(grid)
        targets = [part for part in parts if part["color"] == 1 and len(part["cells"]) == 9]
        decorations = [part for part in parts if part["color"] != 1]
        if mutation == "remove_target_cell":
            r, c = min(targets[0]["cells"])
            grid[r][c] = 0
        elif mutation == "remove_decoration":
            for r, c in decorations[0]["cells"]:
                grid[r][c] = 0
        elif mutation == "add_third_decor_color":
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == 0:
                        grid[r][c] = 9
                        break
                else:
                    continue
                break
        elif mutation == "merge_two_blue_components":
            a, b = [part for part in parts if part["color"] == 1][:2]
            ar, ac = min(a["cells"])
            br, bc = min(b["cells"])
            # A Manhattan path intentionally merges components and violates the grammar.
            r, c = ar, ac
            while r != br:
                grid[r][c] = 1
                r += 1 if br > r else -1
            while c != bc:
                grid[r][c] = 1
                c += 1 if bc > c else -1
            grid[r][c] = 1
    assert gen.self_check(grid), mutation


def test_declared_mutation_fixtures_are_all_rejected():
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name

@pytest.mark.parametrize("profile", PROFILES)
def test_difficulty_bands_are_not_dead(profile):
    variants = {
        json.dumps(gen.generate(211, 17, difficulty=band, scene_profile=profile), separators=(",", ":"))
        for band in ("easy", "medium", "hard")
    }
    assert len(variants) >= 2
