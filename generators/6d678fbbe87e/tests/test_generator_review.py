"""Regression contract for the 6d678fbbe87e repair.

These tests were added before the implementation change.  They encode the
canonical local-window rule, exact override surface, and the curriculum defect
reported by the retained review evidence.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "6d678fbbe87e"
ROOT = find_root(__file__)
GEN, _SOURCE, _DIGEST = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
EXPECTED_RIVALS = {
    "isolated_l_components_only",
    "component_bbox_completion",
    "one_completion_per_color",
    "repeat_until_stable",
}


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_authority_pin_and_honest_public_contract():
    assert GEN.RULE_HASH == "e0165fc03ab4"
    assert GEN.VERSION == "3.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.AXES == {
        "grid_h": {
            "type": "int",
            "default": "canonical-anchored 4..8",
            "valid": "4..8",
        },
        "grid_w": {
            "type": "int",
            "default": "canonical-anchored 5..10",
            "valid": "5..10",
        },
    }
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert set(GEN.SEMANTIC_RIVALS) == EXPECTED_RIVALS
    assert set(GEN.CANONICAL_SHORTCUTS) == EXPECTED_RIVALS
    assert set(GEN.LESSON_COMPETITORS) == EXPECTED_RIVALS


def test_canonical_pairs_are_accepted_and_match_the_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_shortcut_really_fits_all_canonical_pairs():
    pairs = _canonical_pairs()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("shape", [(4, 5), (4, 10), (8, 5), (8, 10)])
def test_exact_size_overrides_work_at_all_boundaries_in_every_band(difficulty, shape):
    requested = {"grid_h": shape[0], "grid_w": shape[1]}
    grid = GEN.generate(17, 9, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert (len(grid), len(grid[0])) == shape


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((0.0, 0), {}),
        (("0", 0), {}),
        ((0, True), {}),
        ((0, 0.0), {}),
        ((0, "0"), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "impossible"}),
        ((0, 0), {"typo": 1}),
        ((0, 0), {"grid_h": 3}),
        ((0, 0), {"grid_h": 9}),
        ((0, 0), {"grid_w": 4}),
        ((0, 0), {"grid_w": 11}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_h": 4.0}),
        ((0, 0), {"grid_w": "5"}),
    ],
)
def test_invalid_scalars_unknown_axes_and_out_of_range_values_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize("difficulty", BANDS)
def test_generated_schedule_is_deterministic_valid_and_diverse(difficulty):
    seen = set()
    profiles = set()
    canonical_profiles = set()
    for sample_index in range(64):
        grid = GEN.generate(20261012, sample_index, difficulty=difficulty)
        assert grid == GEN.generate(20261012, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) != grid
        assert set(value for row in grid for value in row if value) and len(
            {value for row in grid for value in row}
        ) == 4
        profile = GEN.schedule_profile(20261012, sample_index, difficulty=difficulty)
        assert profile in GEN.SCHEDULE_PROFILES
        profiles.add(profile)
        seen.add(tuple(tuple(row) for row in grid))
        if (len(grid), len(grid[0])) in {(4, 5), (4, 6)}:
            canonical_profiles.add((len(grid), len(grid[0]), 4))
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert {(4, 5, 4), (4, 6, 4)} <= canonical_profiles
    assert len(seen) >= 56


@pytest.mark.parametrize("difficulty", BANDS)
def test_connected_schedule_profiles_refute_every_declared_rival(difficulty):
    for sample_index in (1, 2, 3):
        grid = GEN.generate(73, sample_index, difficulty=difficulty)
        expected = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["connected_multiwindow_component"](grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, (sample_index, name)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("start", range(12))
def test_every_consecutive_four_pair_lesson_survives_every_query_rotation(difficulty, start):
    grids = [GEN.generate(991, start + offset, difficulty=difficulty) for offset in range(4)]
    pairs = [_pair(grid) for grid in grids]
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                start,
                query_index,
                name,
            )


def test_retained_connected_component_witness_separates_object_shortcuts():
    grid = [
        [4, 4, 0, 0, 0],
        [4, 0, 0, 0, 0],
        [4, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    expected = GEN.rule_mirror(grid)
    assert expected[1][1] == 4
    assert GEN.SEMANTIC_RIVALS["isolated_l_components_only"](grid) != expected
    assert GEN.SEMANTIC_RIVALS["component_bbox_completion"](grid) != expected
    assert GEN.SEMANTIC_RIVALS["repeat_until_stable"](grid) != expected


def test_declared_witness_to_rival_mapping_is_executable():
    assert GEN.WITNESS_RIVALS == {
        "connected_multiwindow_component": sorted(EXPECTED_RIVALS),
    }
    grids = [GEN.generate(33, index) for index in (1, 2, 3)]
    witness = GEN.SEMANTIC_WITNESSES["connected_multiwindow_component"]
    assert all(witness(grid) for grid in grids)
    for rival_name in GEN.WITNESS_RIVALS["connected_multiwindow_component"]:
        assert any(
            GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
            for grid in grids
        )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 5 for _ in range(4)],
        [[10] * 5 for _ in range(4)],
        [[0] * 4 for _ in range(4)],
        [[0] * 5 for _ in range(3)],
    ],
)
def test_malformed_or_out_of_contract_grids_return_diagnostics(bad):
    assert GEN.self_check(bad)


def test_validator_rejects_noop_and_missing_colour_instances():
    blank = [[0] * 5 for _ in range(4)]
    one_colour = [
        [1, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    assert GEN.self_check(blank)
    assert GEN.self_check(one_colour)


def test_oracles_and_rivals_do_not_mutate_inputs():
    grid = GEN.generate(22, 1)
    original = deepcopy(grid)
    GEN.rule_mirror(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_broad_profiles_make_the_difficulty_knob_observable_without_narrowing_overrides():
    grids = {
        difficulty: tuple(tuple(row) for row in GEN.generate(5150, 2, difficulty=difficulty))
        for difficulty in ("easy", "medium", "hard")
    }
    assert len(set(grids.values())) == 3
    # Exact overrides remain legal across all bands despite band-sensitive defaults.
    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(5150, 2, difficulty=difficulty, grid_h=8, grid_w=5)
        assert GEN.observe_overrides(grid) == {"grid_h": 8, "grid_w": 5}
