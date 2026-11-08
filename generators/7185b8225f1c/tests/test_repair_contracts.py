from __future__ import annotations

import copy
import itertools

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "7185b8225f1c"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def labeled(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_a_literal_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1, None])
def test_sample_index_requires_a_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, sample_index)


def test_declared_cell_halo_shortcut_fits_every_labeled_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["cell_halo_only"]
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == pair["output"]


def test_small_concave_input_is_an_exact_cell_halo_counterexample():
    grid = [[0] * 8 for _ in range(8)]
    grid[0][0] = 2
    grid[3][3] = grid[4][3] = grid[4][4] = 2
    expected = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["cell_halo_only"](grid)
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["full_bbox_not_cell_halo"](grid)
    assert expected != rival
    assert expected[2][5] == 3 and rival[2][5] == 0


def test_every_scheduled_witness_slot_actually_refutes_cell_halo():
    witness = GEN.SEMANTIC_WITNESSES["full_bbox_not_cell_halo"]
    for band, seed, index in itertools.product(
        (None, "easy", "medium", "hard"), range(8), range(12)
    ):
        grid = GEN.generate(seed, index, difficulty=band)
        profile = GEN.schedule_profile(seed, index, band)
        if profile == "bbox_witness":
            assert witness(grid), (band, seed, index, GEN.observe_overrides(grid))


def test_every_consecutive_four_pair_window_survives_all_query_rotations():
    assert GEN.EXAMPLES_NEEDED == 3
    for band, seed, start in itertools.product(
        (None, "easy", "medium", "hard"), range(6), range(8)
    ):
        pairs = [labeled(GEN.generate(seed, start + offset, difficulty=band)) for offset in range(4)]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == [], (
                band,
                seed,
                start,
                query_index,
            )
            assert any(
                GEN.LESSON_COMPETITORS["cell_halo_only"](demo["input"])
                != demo["output"]
                for demo in demos
            )


def test_explicit_scene_profile_override_wins_over_teaching_schedule():
    for index, profile in enumerate(GEN.SCENE_PROFILES):
        grid = GEN.generate(90210, index, difficulty="medium", scene_profile=profile)
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def test_default_schedule_retains_all_profiles_and_public_support():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(50_000 + seed, seed, difficulty=band) for seed in range(1200)]
        profiles = [GEN.observe_overrides(grid)["scene_profile"] for grid in grids]
        assert set(profiles) == set(GEN.SCENE_PROFILES)
        assert sum(profile in GEN.PUBLIC_PROFILES for profile in profiles) >= 300
