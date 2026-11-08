"""Focused regressions for the 2026-10-22 review repair."""
from __future__ import annotations

from collections import Counter

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "97bcb3b9194e"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PROFILES = {
    (12, 11, 4),
    (21, 18, 4),
    (22, 15, 4),
    (22, 20, 4),
    (22, 21, 4),
    (22, 25, 4),
}


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize("seed", [True, 1.5, "1", None])
def test_generate_rejects_coerced_seed_values(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, -1, 1.5, "1", None])
def test_generate_rejects_coerced_or_negative_sample_indices(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, sample_index, difficulty="easy")


@pytest.mark.parametrize("difficulty", [True, 0, 1.0, "extreme"])
def test_generate_rejects_unknown_or_non_string_difficulties(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "n_boxes", "winner_marks"])
@pytest.mark.parametrize("bad", [True, 3.75, "4"])
def test_integer_axes_reject_bool_float_and_string_coercion(axis, bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty="easy", **{axis: bad})


@pytest.mark.parametrize(
    "axis,bad",
    [
        ("mark_palette", True),
        ("mark_palette", 4),
        ("winner_position", False),
        ("winner_position", 0),
    ],
)
def test_choice_axes_require_exact_strings(axis, bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty="easy", **{axis: bad})


def test_default_schedule_has_exact_canonical_profile_anchors_in_every_band():
    expected_sequence = [
        (12, 11, 4),
        (21, 18, 4),
        (22, 15, 4),
        (22, 20, 4),
        (22, 21, 4),
        (22, 25, 4),
    ]
    for band in ("easy", "medium", "hard"):
        profiles = [
            _profile(GEN.generate(70_000, sample_index, difficulty=band))
            for sample_index in range(0, 36, 6)
        ]
        assert profiles == expected_sequence
        assert set(profiles) == CANONICAL_PROFILES


def test_mark_palette_domain_includes_noncanonical_counterexamples():
    noncanonical = {
        name
        for name, colors in GEN.MARK_PALETTES.items()
        if not set(colors).issubset({4, 6})
    }
    assert len(noncanonical) >= 3
    grids = [GEN.generate(777, index, difficulty="medium") for index in range(36)]
    observed = [GEN.observe_overrides(grid)["mark_palette"] for grid in grids]
    assert set(observed) == set(GEN.MARK_PALETTES)
    assert all(observed.count(name) >= 1 for name in noncanonical)
    counterexamples = [
        index
        for index, grid in enumerate(grids)
        if GEN._count_only_4_6(grid) != GEN.rule_mirror(grid)
    ]
    assert counterexamples
    assert any(index < 12 for index in counterexamples)


def test_semantic_contract_binds_canonical_shortcut_and_generated_witnesses():
    assert GEN.strict_canonical_like(GEN.generate(1, 0, difficulty="easy")) == []
    assert GEN.CANONICAL_SHORTCUTS["count_only_4_6"] is GEN._count_only_4_6
    assert GEN.SEMANTIC_RIVALS["count_only_4_6"] is GEN._count_only_4_6
    assert GEN.LESSON_COMPETITORS["count_only_4_6"] is GEN._count_only_4_6
    assert GEN.WITNESS_RIVALS["noncanonical_marks_refute_4_6_only"] == [
        "count_only_4_6"
    ]

    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._count_only_4_6(pair["input"]) == pair["output"]

    witnesses = []
    for index in range(48):
        grid = GEN.generate(91_337, index, difficulty="hard")
        fires = GEN.SEMANTIC_WITNESSES["noncanonical_marks_refute_4_6_only"](grid)
        if fires:
            witnesses.append(grid)
            assert GEN._count_only_4_6(grid) != GEN.rule_mirror(grid)
    assert len(witnesses) >= 12


def test_repaired_default_population_stays_deterministic_and_varied():
    grids = [GEN.generate(4000 + i, i, difficulty="medium") for i in range(120)]
    assert len({_frozen(grid) for grid in grids}) == len(grids)
    assert all(GEN.self_check(grid) == [] for grid in grids)
    palettes = Counter(GEN.observe_overrides(grid)["mark_palette"] for grid in grids)
    assert set(palettes) == set(GEN.MARK_PALETTES)
    assert palettes["canonical"] >= 15

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_teaches_noncanonical_color_counting_under_rotation(band):
    """Any held-out member of a four-pair lesson leaves a rebuttal in demos."""
    grids = [GEN.generate(51_337, index, difficulty=band) for index in range(72)]
    witness = GEN.SEMANTIC_WITNESSES["noncanonical_marks_refute_4_6_only"]
    fires = [bool(witness(grid)) for grid in grids]
    for start in range(len(fires) - 3):
        window = fires[start : start + 4]
        assert sum(window) >= 2, (band, start, window)
