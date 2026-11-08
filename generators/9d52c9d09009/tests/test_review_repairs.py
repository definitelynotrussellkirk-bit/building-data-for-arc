from __future__ import annotations

import random

import pytest

from reviewer_support import find_root, load_selected_generator


TASK = "9d52c9d09009"
ROOT = find_root(__file__)
MODULE, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK, root=ROOT)


def _frozen(grid):
    return tuple(map(tuple, grid))


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_literal_integers(seed):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_rejects_invalid_scalars(sample_index):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(1, sample_index)


def test_public_morphology_keeps_a_canonical_canvas_profile_in_every_band():
    for profile in MODULE.PUBLIC_PROFILES:
        canonical = MODULE._PUBLIC_INPUTS[profile]
        expected_shape = (len(canonical), len(canonical[0]))
        for difficulty in ("easy", "medium", "hard"):
            scene = MODULE._public_scene(profile, difficulty, random.Random(10_000 + len(profile)))
            assert (len(scene), len(scene[0])) == expected_shape
            assert MODULE.canonical_family_signature(scene) == profile
            assert _frozen(scene) != _frozen(canonical)


def test_diagonal_zero_contact_distinguishes_four_from_eight_connectivity():
    grid = [
        [8, 8, 8, 8],
        [8, 0, 8, 8],
        [8, 8, 0, 8],
        [8, 8, 8, 8],
    ]
    intended = MODULE.rule_mirror(grid)
    rival = MODULE._eight_connected_zero_regions_rule(grid)
    assert intended != rival
    assert intended[0][0] == 2
    assert rival[0][0] == 1
    assert MODULE._has_four_vs_eight_connectivity_witness(grid)


def test_every_general_profile_emits_a_connectivity_witness():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(4):
            grid = MODULE.generate(30_000 + seed, 2 * seed + 1, scene_profile=profile)
            assert MODULE.self_check(grid) == []
            assert MODULE._has_four_vs_eight_connectivity_witness(grid)
            assert MODULE.rule_mirror(grid) != MODULE._eight_connected_zero_regions_rule(grid)


def test_declared_semantic_contract_names_the_canonical_shortcut():
    name = "eight_connected_zero_regions"
    assert MODULE.SEMANTIC_RIVALS[name] is MODULE._eight_connected_zero_regions_rule
    assert MODULE.CANONICAL_SHORTCUTS[name] is MODULE._eight_connected_zero_regions_rule
    assert MODULE.LESSON_COMPETITORS[name] is MODULE._eight_connected_zero_regions_rule
    assert MODULE.SEMANTIC_WITNESSES["four_vs_eight_connectivity"] is MODULE._has_four_vs_eight_connectivity_witness
    assert MODULE.WITNESS_RIVALS["four_vs_eight_connectivity"] == [name]
    assert MODULE.strict_canonical_like(MODULE.generate(41, 0)) == []


def test_two_step_schedule_refutes_the_rival_before_any_general_query():
    assert MODULE.LESSON_SCHEDULE_PERIOD == 2
    for start in range(MODULE.LESSON_SCHEDULE_PERIOD):
        classes = [MODULE.schedule_profile(0, start + offset, "medium") for offset in range(4)]
        if classes[-1] == "general":
            assert "general" in classes[:-1]
        assert classes == ["public" if (start + offset) % 2 == 0 else "general" for offset in range(4)]


def test_exact_scene_profile_override_still_bypasses_schedule():
    for sample_index, profile in enumerate(MODULE.SCENE_PROFILES):
        grid = MODULE.generate(87, sample_index, difficulty="hard", scene_profile=profile)
        assert MODULE.canonical_family_signature(grid) == profile
