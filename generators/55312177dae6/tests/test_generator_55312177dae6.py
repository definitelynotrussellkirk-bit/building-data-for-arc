"""Focused structural, authority and curriculum regressions for 55312177dae6."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    authority_output,
    canonical_pairs,
    load_generator,
    observed,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


def test_contract_surface_pins_authority_and_only_observable_axes():
    assert GEN.RULE_HASH == "39919c9ecf3d"
    assert GEN.VERSION == "4.0.0"
    assert set(GEN.AXES) == {
        "grid_h", "grid_w", "n_distractors", "target_area", "match_rotation"
    }
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.HELPFUL_TEXTURES == ()
    assert callable(GEN.observe_overrides)
    assert callable(GEN.rule_mirror)
    assert callable(GEN.lesson_identifiable)


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert authority_output(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 10, "n_distractors": 1,
         "target_area": 3, "match_rotation": 1},
        {"grid_h": 8, "grid_w": 10, "n_distractors": 2,
         "target_area": 5, "match_rotation": 3},
        {"grid_h": 16, "grid_w": 18, "n_distractors": 2,
         "target_area": 4, "match_rotation": 2},
    ],
)
def test_exact_override_boundaries_are_realized_in_every_band(band, requested):
    grid = GEN.generate(314159, 17, difficulty=band, **requested)
    assert GEN.self_check(grid, meta=requested) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert observed(grid) == requested
    assert GEN.rule_mirror(grid) == authority_output(grid)
    assert GEN.generate(314159, 17, difficulty=band, **requested) == grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1}, {"grid_h": 7}, {"grid_h": 17},
        {"grid_w": 9}, {"grid_w": 19}, {"n_distractors": 0},
        {"n_distractors": 3}, {"target_area": 2}, {"target_area": 6},
        {"match_rotation": 0}, {"match_rotation": 4}, {"grid_h": True},
        {"target_area": 4.0}, {"match_rotation": "1"},
    ],
)
def test_unknown_and_invalid_controls_fail_loudly(kwargs):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **kwargs)


def test_invalid_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="expert")


def test_self_check_rejects_known_authority_crashes_and_impostors():
    blank = [[0] * 10 for _ in range(8)]
    singleton = copy.deepcopy(blank)
    singleton[2][2] = 1
    solid = copy.deepcopy(blank)
    for row in range(2, 4):
        for col in range(2, 4):
            solid[row][col] = 1
    no_match = copy.deepcopy(blank)
    for row, col in ((1, 1), (1, 5), (5, 2)):
        no_match[row][col] = 1
    all_same = copy.deepcopy(blank)
    tri = ((0, 0), (1, 0), (1, 1))
    for top, left in ((0, 0), (0, 5), (5, 3)):
        for row, col in tri:
            all_same[top + row][left + col] = 1
    for grid in (blank, singleton, solid, no_match, all_same):
        assert GEN.self_check(grid), grid


def test_default_distribution_is_strict_deterministic_and_profile_supported():
    canonical_sizes = {(8, 10), (9, 11), (10, 12)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seen_sizes = set()
        seen_profiles = set()
        for index in range(80):
            seed = 10_000 * (band_index + 1) + index
            first = GEN.generate(seed, index, difficulty=band)
            second = GEN.generate(seed, index, difficulty=band)
            assert first == second
            assert first is not second
            assert GEN.self_check(first) == []
            assert GEN.strict_canonical_like(first) == []
            assert GEN.rule_mirror(first) == authority_output(first)
            seen_sizes.add((len(first), len(first[0])))
            seen_profiles.add(GEN.schedule_profile(seed, index, band))
        assert canonical_sizes & seen_sizes
        assert seen_profiles == set(GEN.SCHEDULE_PROFILES)


def test_semantic_witnesses_fire_and_named_rivals_disagree():
    seen = set()
    for index in range(160):
        grid = GEN.generate(50_000 + index, index, difficulty="medium")
        intended = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            seen.add(witness_name)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != intended
    assert seen == set(GEN.SEMANTIC_WITNESSES)


def test_declared_canonical_shortcuts_really_fit_canonical_pairs():
    assert GEN.CANONICAL_SHORTCUTS
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_every_cyclic_lesson_window_is_identifiable():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                index = start + offset
                grid = GEN.generate(70_000 + 100 * band_index + start, index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query = GEN.generate(80_000 + start, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            assert GEN.lesson_identifiable(demos, {"input": query}) == []


def test_generation_does_not_touch_global_random_state_or_alias_results():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(90_000, 11, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(90_000, 11, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_target_class_is_unique_and_exactly_paired_across_many_draws():
    for index in range(240):
        grid = GEN.generate(120_000 + index, index, difficulty=BANDS[index % len(BANDS)])
        info = analyze(grid)
        assert len(info["target_indices"]) == 2
        assert all(count == 1 for key, count in info["counts"].items() if key != info["target_key"])
