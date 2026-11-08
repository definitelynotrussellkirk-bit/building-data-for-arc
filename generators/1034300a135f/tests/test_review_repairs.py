"""Regression checks for the review repair of generator 1034300a135f."""
from __future__ import annotations

import importlib
import itertools

import pytest


TASK = "1034300a135f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_generate_and_schedule_reject_nonliteral_seed(bad):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad, 0)
    with pytest.raises(TypeError, match="seed"):
        GEN.schedule_profile(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_generate_and_schedule_reject_nonliteral_sample_index(bad):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(0, bad)
    with pytest.raises(TypeError, match="sample_index"):
        GEN.schedule_profile(0, bad)


def test_generate_and_schedule_reject_negative_sample_index():
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.generate(0, -1)
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.schedule_profile(0, -1)


def test_default_schedule_is_rotation_safe_and_covers_every_profile():
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 2 * (len(GEN.SCENE_PROFILES) - 1)
    assert set(GEN.SCHEDULE_PROFILES) == set(GEN.SCENE_PROFILES)

    scheduled = [
        GEN.schedule_profile(17, index, difficulty="medium")
        for index in range(GEN.LESSON_SCHEDULE_PERIOD)
    ]
    assert set(scheduled) == set(GEN.SCENE_PROFILES)
    assert scheduled.count("teaching_combined") == GEN.LESSON_SCHEDULE_PERIOD // 2

    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        profiles = [
            GEN.schedule_profile(17, start + offset, difficulty="medium")
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        for held_out in range(len(profiles)):
            demos = profiles[:held_out] + profiles[held_out + 1 :]
            assert "teaching_combined" in demos, (start, held_out, profiles)


def test_default_generate_follows_schedule_but_override_remains_exact():
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(GEN.LESSON_SCHEDULE_PERIOD):
            grid = GEN.generate(29, index, difficulty=difficulty)
            assert GEN.observe_overrides(grid) == {
                "scene_profile": GEN.schedule_profile(29, index, difficulty)
            }
        for profile in GEN.SCENE_PROFILES:
            grid = GEN.generate(29, 11, difficulty=difficulty, scene_profile=profile)
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def test_teaching_profile_is_lawful_and_refutes_every_declared_rival():
    expected_rivals = {
        "reverse_equal_distance_ties",
        "use_raw_edge_distance_as_ring_index",
        "extend_last_color_to_center",
        "ignore_zero_markers",
        "deduplicate_marker_colors",
        "sort_marker_colors_numerically",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "reverse_equal_distance_ties",
        "use_raw_edge_distance_as_ring_index",
        "extend_last_color_to_center",
        "deduplicate_marker_colors",
    }

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(24):
            grid = GEN.generate(
                seed,
                seed * 17,
                difficulty=difficulty,
                scene_profile="teaching_combined",
            )
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": "teaching_combined"}
            truth = GEN.rule_mirror(grid)
            assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
            assert all(rival(grid) != truth for rival in GEN.SEMANTIC_RIVALS.values())


def test_witness_claims_are_executable_and_sound_on_generated_support():
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    seen = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for difficulty in ("easy", "medium", "hard"):
        for index in range(GEN.LESSON_SCHEDULE_PERIOD * 2):
            grid = GEN.generate(53, index, difficulty=difficulty)
            truth = GEN.rule_mirror(grid)
            for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    seen[witness_name] += 1
                    for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                        assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(seen.values()), seen


def test_declared_canonical_shortcuts_reproduce_every_canonical_pair():
    for profile in GEN.PUBLIC_PROFILES:
        grid = GEN.generate(7, 13, scene_profile=profile)
        truth = GEN.rule_mirror(grid)
        for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
            assert shortcut(grid) == truth, (profile, name)


def test_every_scheduled_window_and_rotation_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(GEN.generate(71, start + offset, difficulty=difficulty))
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(pairs)):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                )
                for rival_name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (difficulty, start, query_index, rival_name)


def test_lesson_hook_names_a_surviving_query_changing_rival():
    teaching = _pair(GEN.generate(5, 0, scene_profile="teaching_combined"))
    ordinary = [
        _pair(GEN.generate(5, 1 + 2 * index, scene_profile=profile))
        for index, profile in enumerate(GEN.PUBLIC_PROFILES[:3])
    ]
    rival_name = "reverse_equal_distance_ties"
    rival = GEN.LESSON_COMPETITORS[rival_name]
    assert all(rival(pair["input"]) == pair["output"] for pair in ordinary)
    assert rival(teaching["input"]) != teaching["output"]
    reasons = GEN.lesson_identifiable(ordinary, teaching)
    assert any(rival_name in reason for reason in reasons)


def test_teaching_profile_changes_a_nonzero_marker_cell():
    """Refute generic 'only the background object changes' attribution."""
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(24):
            grid = GEN.generate(
                seed,
                seed * 31,
                difficulty=difficulty,
                scene_profile="teaching_combined",
            )
            facts = GEN._analysis(grid)["facts"]
            truth = GEN.rule_mirror(grid)
            assert any(
                marker["color"] != 0
                and truth[marker["row"]][marker["col"]] != marker["color"]
                for marker in facts["markers"]
            ), (difficulty, seed, facts)
