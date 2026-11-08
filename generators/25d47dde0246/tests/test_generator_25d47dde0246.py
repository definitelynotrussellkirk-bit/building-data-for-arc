from __future__ import annotations

import hashlib
import json
import random
import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "25d47dde0246"
ROOT = find_root(__file__)
MODULE, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _canonical_row()["train"] + _canonical_row()["test"]
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 5
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(5000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_joint_bbox_spans_disconnected_objects_and_preserves_internal_zeros():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 8, 0],
        [0, 0, 0, 0, 8, 8, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert MODULE.rule_mirror(grid) == [
        [2, 2, 0, 0, 0],
        [2, 0, 0, 0, 8],
        [0, 0, 0, 8, 8],
    ]


def test_oracle_defines_empty_fallback_but_training_checker_rejects_it():
    empty = [[0] * 6 for _ in range(5)]
    assert MODULE.rule_mirror(empty) == [[0]]
    assert MODULE.self_check(empty)


def test_boundary_profiles_still_remove_padding_on_other_axes():
    for profile in ("touches_horizontal_edge", "touches_vertical_edge"):
        grid = MODULE.generate(123, 456, scene_profile=profile)
        output = MODULE.rule_mirror(grid)
        assert len(output) < len(grid) or len(output[0]) < len(grid[0])
        assert any(value == 0 for row in output for value in row)


def test_sparse_and_hole_profiles_retain_meaningful_zero_structure():
    for profile in ("sparse_bbox", "internal_hole"):
        grid = MODULE.generate(456, 789, scene_profile=profile)
        output = MODULE.rule_mirror(grid)
        assert any(value == 0 for row in output for value in row)
        assert any(value != 0 for row in output for value in row)


def test_full_palette_crop_preserves_all_nonzero_colors():
    grid = MODULE.generate(999, 111, scene_profile="full_palette")
    assert {value for row in MODULE.rule_mirror(grid) for value in row if value} == set(range(1, 10))


def test_narrow_profiles_produce_one_dimensional_crops():
    row_grid = MODULE.generate(1, 2, scene_profile="narrow_row")
    col_grid = MODULE.generate(1, 2, scene_profile="narrow_col")
    assert len(MODULE.rule_mirror(row_grid)) == 1
    assert len(MODULE.rule_mirror(col_grid)[0]) == 1


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[1, 0], [1]],
        [[True] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
        [[0] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(3)] + [[0, 0, 0, 5, 0, 0, 0]] + [[0] * 7 for _ in range(3)],
        [[5, 5], [5, 5]],
        [[5] * 7 for _ in range(7)],
    ],
)
def test_self_check_rejects_malformed_or_minimal_impostors(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=10)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


def _labeled_default_window(seed, start, *, difficulty=None):
    pairs = []
    for sample_index in range(start, start + 4):
        grid = MODULE.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    return pairs


def test_declared_largest_component_shortcut_fits_canonical_but_not_joint_bbox_witness():
    rival = MODULE.CANONICAL_SHORTCUTS["largest_component_only"]
    for pair in _canonical_row()["train"] + _canonical_row()["test"]:
        assert rival(pair["input"]) == pair["output"]

    witness = MODULE.generate(91, 7, scene_profile="disconnected_objects")
    assert rival(witness) != MODULE.rule_mirror(witness)
    assert MODULE.SEMANTIC_WITNESSES["joint_bbox_uses_all_components"](witness) is True
    assert MODULE.WITNESS_RIVALS["joint_bbox_uses_all_components"] == ["largest_component_only"]


def test_schedule_contract_declares_the_full_teaching_period():
    assert MODULE.LESSON_SCHEDULE_PERIOD == 4
    assert MODULE.TEACHING_WITNESS_PERIOD == 2
    assert [MODULE.schedule_profile(11, index) for index in range(4)] == [
        "ordinary_mix",
        "joint_bbox_witness",
        "canonical_support",
        "joint_bbox_witness",
    ]


def test_retained_seed_11_window_is_identifiable_after_scheduled_witness():
    pairs = _labeled_default_window(11, 0)
    demo_profiles = [MODULE.observe_overrides(pair["input"])["scene_profile"] for pair in pairs[:3]]
    assert "disconnected_objects" in demo_profiles
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_every_three_consecutive_default_samples_refute_largest_component_shortcut():
    rival = MODULE.LESSON_COMPETITORS["largest_component_only"]
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 11, 97):
            for start in range(12):
                grids = [
                    MODULE.generate(seed, sample_index, difficulty=difficulty)
                    for sample_index in range(start, start + MODULE.EXAMPLES_NEEDED)
                ]
                assert any(rival(grid) != MODULE.rule_mirror(grid) for grid in grids), (
                    difficulty,
                    seed,
                    start,
                    [MODULE.observe_overrides(grid) for grid in grids],
                )


def test_schedule_reserves_exact_canonical_support_in_each_period():
    assert MODULE.LESSON_SCHEDULE_PERIOD == 4
    assert [MODULE.schedule_profile(11, index) for index in range(4)] == [
        "ordinary_mix",
        "joint_bbox_witness",
        "canonical_support",
        "joint_bbox_witness",
    ]
    for difficulty in (None, "easy", "medium", "hard"):
        grid = MODULE.generate(123, 2, difficulty=difficulty)
        assert MODULE.observe_overrides(grid)["scene_profile"] in MODULE.PUBLIC_PROFILES


def test_every_query_rotation_keeps_a_shortcut_refuting_demo():
    rival = MODULE.LESSON_COMPETITORS["largest_component_only"]
    lesson_size = MODULE.EXAMPLES_NEEDED + 1
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 11, 97):
            for start in range(MODULE.LESSON_SCHEDULE_PERIOD):
                grids = [
                    MODULE.generate(seed, sample_index, difficulty=difficulty)
                    for sample_index in range(start, start + lesson_size)
                ]
                for query_index in range(lesson_size):
                    demos = [grid for index, grid in enumerate(grids) if index != query_index]
                    assert any(rival(grid) != MODULE.rule_mirror(grid) for grid in demos), (
                        difficulty,
                        seed,
                        start,
                        query_index,
                        [MODULE.observe_overrides(grid) for grid in grids],
                    )


def test_explicit_profile_override_wins_on_the_scheduled_teaching_slot():
    grid = MODULE.generate(123, 1, scene_profile="narrow_row")
    assert MODULE.observe_overrides(grid) == {"scene_profile": "narrow_row"}


def test_lesson_identifiable_rejects_incorrect_demo_label_and_malformed_query():
    pairs = _labeled_default_window(11, 0)
    corrupted = [
        {"input": pair["input"], "output": [row[:] for row in pair["output"]]}
        for pair in pairs[:3]
    ]
    corrupted[0]["output"][0][0] = (corrupted[0]["output"][0][0] + 1) % 10
    reasons = MODULE.lesson_identifiable(corrupted, pairs[3])
    assert any("demo 0 output" in reason for reason in reasons)

    reasons = MODULE.lesson_identifiable(pairs[:3], {"output": [[0]]})
    assert any("query must contain an input grid" in reason for reason in reasons)
