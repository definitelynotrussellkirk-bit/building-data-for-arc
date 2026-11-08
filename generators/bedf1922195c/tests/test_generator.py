"""Focused regressions for the bedf1922195c curriculum repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "bedf1922195c"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    any_color_odd_straight_rival,
    branch_signature,
    ignore_parity_rival,
    ignore_straightness_rival,
    only_lengths_3_or_5_rival,
    has_length_seven_blue_segment,
    intended_output,
    load_generator,
    palette_size,
    qualifying_blue_segments,
)

gen = load_generator(SOURCE)
ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
EXPECTED_RIVALS = {
    "any_color_odd_straight",
    "ignore_parity",
    "ignore_straightness",
    "only_lengths_3_or_5",
}
EXPECTED_BRANCHES = {
    "parity_shape": (True, True, False),
    "shape_color": (False, True, True),
    "color_parity": (True, False, True),
}


def test_rule_pin_and_selected_authority_are_exactly_synchronized():
    assert gen.RULE_HASH == "6a1fd35b307c"
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    canonical = next(
        json.loads(line)
        for line in canonical_path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    authority_path = ROOT / "shared/data/base/solutions/banks/53ccebf2a36f/E120__bedf1922195c.json"
    authority = json.loads(authority_path.read_text())
    assert authority["racket_target"]["raw_code"] == canonical["program_solution"]
    assert authority["racket_target"]["target_code"] == canonical["program_solution"]


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_axis_surface_is_one_exact_observable_scene_profile():
    assert tuple(gen.AXES) == ("scene_profile",)
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert set(gen.SCHEDULE_PROFILES) == set(gen.AXES["scene_profile"]["valid"].split("|"))
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", BANDS)
def test_every_profile_override_is_exact_in_every_band(band):
    for profile in gen.SCHEDULE_PROFILES:
        grid = gen.generate(41, 7, difficulty=band, scene_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert grid == gen.generate(41, 7, difficulty=band, scene_profile=profile)


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": 1},
    {"scene_profile": "not-a-profile"},
])
def test_invalid_and_unknown_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", BANDS)
def test_every_three_demo_window_and_every_rotation_refute_all_rivals(band):
    for start in range(9):
        grids = [gen.generate(719, start + offset, difficulty=band) for offset in range(4)]
        pairs = [{"input": grid, "output": intended_output(grid)} for grid in grids]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_has_canonical_profile_support_and_paired_counterexamples(band):
    canonical_profiles = {(8, 10, 4), (9, 9, 3), (9, 10, 3), (9, 11, 3), (10, 10, 3)}
    observed_profiles = set()
    observed_branches = set()
    for index in range(18):
        grid = gen.generate(811, index, difficulty=band)
        observed_profiles.add((len(grid), len(grid[0]), palette_size(grid)))
        observed_branches.add(branch_signature(grid))
        assert len(qualifying_blue_segments(grid)) >= 2
        assert has_length_seven_blue_segment(grid)
        assert sum(branch_signature(grid)) == 2
        expected = intended_output(grid)
        assert expected != grid
        assert gen.rule_mirror(grid) == expected
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[gen.RIVAL_WITNESSES[name]](grid):
                assert rival(grid) != expected
    assert observed_profiles & canonical_profiles
    assert observed_branches == set(EXPECTED_BRANCHES.values())


def test_canonical_shortcuts_fit_every_public_pair_and_names_are_bound():
    assert set(gen.CANONICAL_SHORTCUTS) == EXPECTED_RIVALS
    assert set(gen.SEMANTIC_RIVALS) == EXPECTED_RIVALS
    assert set(gen.LESSON_COMPETITORS) == EXPECTED_RIVALS
    assert set(gen.RIVAL_WITNESSES) == EXPECTED_RIVALS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


def test_declared_rivals_match_independent_probes():
    probes = {
        "any_color_odd_straight": any_color_odd_straight_rival,
        "ignore_parity": ignore_parity_rival,
        "ignore_straightness": ignore_straightness_rival,
        "only_lengths_3_or_5": only_lengths_3_or_5_rival,
    }
    for profile in gen.SCHEDULE_PROFILES:
        grid = gen.generate(2026, 5, scene_profile=profile)
        for name, independent in probes.items():
            assert gen.SEMANTIC_RIVALS[name](grid) == independent(grid)


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True] * 10 for _ in range(8)],
    [[1] * 10 for _ in range(8)],
    [[0] * 10 for _ in range(8)],
    [[0, 0, 0], [0, 1, 0], [0, 0, 3]],
    [[0, 0, 0], [1, 1, 1], [0, 0, 3]],
])
def test_malformed_or_rule_hiding_grids_return_reasons_not_exceptions(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", BANDS)
def test_distribution_is_deterministic_pure_and_diverse(band):
    unique = set()
    profiles = set()
    for index in range(96):
        grid = gen.generate(9000 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(9000 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        saved = deepcopy(grid)
        output = gen.rule_mirror(grid)
        for rival in gen.LESSON_COMPETITORS.values():
            _ = rival(grid)
        assert grid == saved
        assert output is not grid
        assert all(out_row is not in_row for out_row, in_row in zip(output, grid))
        unique.add(tuple(map(tuple, grid)))
        profiles.add(gen.observe_overrides(grid)["scene_profile"])
    assert len(unique) >= 90
    assert profiles == set(gen._PROFILES_BY_BAND[gen._band(band)])
