from __future__ import annotations

import json
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "de49e9901e3a"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _profiles():
    return {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    }


def _in_envelope(profile, canonical_profiles):
    columns = list(zip(*canonical_profiles))
    return all(min(values) <= value <= max(values) for value, values in zip(profile, columns))


def test_canonical_pairs_match_independent_bbox_oracle():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._rule_bbox_fill(pair["input"]) == pair["output"]


def test_canonical_fitting_cross_only_rival_is_real_and_refuted_by_witness():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert GEN._rival_cross_only(pair["input"]) == pair["output"]

    counterexample_path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "cross_only_shortcut.json"
    )
    counterexample = json.loads(counterexample_path.read_text())
    witness = counterexample["input"]
    assert GEN._has_non_cross_object(witness)
    assert GEN.self_check(witness) == []
    assert GEN._rule_bbox_fill(witness) == counterexample["intended_output"]
    assert GEN._rival_cross_only(witness) == counterexample["shortcut_output"]
    assert counterexample["shortcut_output"] != counterexample["intended_output"]


def test_every_default_draw_contains_a_non_cross_witness_and_is_lawful():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(112358, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN._has_non_cross_object(grid)


def test_default_schedule_meets_profile_floor_in_every_band():
    canonical_profiles = _profiles()
    for difficulty in ("easy", "medium", "hard"):
        profiles = []
        for sample_index in range(20):
            grid = GEN.generate(271828, sample_index, difficulty=difficulty)
            profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        exact = sum(profile in canonical_profiles for profile in profiles)
        envelope = sum(_in_envelope(profile, canonical_profiles) for profile in profiles)
        assert exact >= 1, (difficulty, profiles)
        assert envelope >= 5, (difficulty, profiles)


def test_all_exact_controls_are_observable_at_smallest_joint_case():
    for n_colors in (1, 2):
        grid = GEN.generate(
            314159,
            7,
            difficulty="hard",
            grid_h=8,
            grid_w=8,
            n_objects=4,
            n_colors=n_colors,
        )
        assert GEN.self_check(grid, difficulty="hard") == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": 8,
            "grid_w": 8,
            "n_objects": 4,
            "n_colors": n_colors,
        }


def test_override_contract_rejects_unknown_invalid_and_out_of_range_values():
    bad_calls = (
        {"unknown_axis": 1},
        {"grid_h": "8"},
        {"grid_h": 7},
        {"grid_w": True},
        {"n_objects": 5},
        {"n_colors": 3},
    )
    for overrides in bad_calls:
        with pytest.raises(ValueError):
            GEN.generate(0, 0, **overrides)

    for difficulty in (True, "impossible"):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, difficulty=difficulty)


def test_public_seed_and_sample_index_controls_are_strict_scalars():
    for bad_seed in (True, False, 1.0, 1.75, "1", None):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(bad_seed, 0)

    for bad_index in (True, False, -1, 1.0, 1.75, "1", None):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, bad_index)
