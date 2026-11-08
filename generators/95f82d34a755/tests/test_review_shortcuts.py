"""Reviewer-added regressions for schedule, shortcut, and API contracts."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

try:
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "95f82d34a755"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_schedule_contract_names_the_complete_five_profile_cycle():
    assert gen.EXAMPLES_NEEDED == len(gen.SCENE_PROFILES)
    assert gen.SCHEDULE_PROFILES == gen.SCENE_PROFILES
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            observed = {
                gen.schedule_profile(123, start + offset, difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            }
            assert observed == set(gen.SCENE_PROFILES)


def test_feature_only_witnesses_are_declared_as_branch_coverage():
    assert set(gen.BRANCH_WITNESSES) == {
        "single_shared_color",
        "multiple_shared_colors",
        "repeated_row_label",
        "repeated_column_label",
        "off_diagonal_match",
        "both_match_and_mismatch",
    }


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    expected = {"canonical_extent_only", "first_two_occurrences_only"}
    assert expected <= set(gen.CANONICAL_SHORTCUTS)
    for name in expected:
        shortcut = gen.CANONICAL_SHORTCUTS[name]
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            assert shortcut(pair["input"]) == pair["output"], name


def test_every_five_demo_window_refutes_both_canonical_shortcuts():
    expected = {"canonical_extent_only", "first_two_occurrences_only"}
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(10):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                source = gen.generate(20261012, start + offset, difficulty=difficulty)
                demos.append((source, gen.rule_mirror(source)))

            assert any(
                len(source) == 8
                and len(source[0]) == 9
                and gen.observe_overrides(source)["scene_profile"] == "multi_shared"
                for source, _output in demos
            )
            for name in expected:
                shortcut = gen.CANONICAL_SHORTCUTS[name]
                assert any(shortcut(source) != output for source, output in demos), name


def test_explicit_dimensions_override_the_extended_schedule_anchor():
    source = gen.generate(
        20261012,
        3,
        difficulty="easy",
        grid_h=4,
        grid_w=5,
        scene_profile="multi_shared",
        palette_band="low",
    )
    assert gen.observe_overrides(source) == {
        "grid_h": 4,
        "grid_w": 5,
        "scene_profile": "multi_shared",
        "palette_band": "low",
    }


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, "1", -1])
def test_generate_rejects_non_strict_or_negative_sample_index(bad_sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, bad_sample_index)


def test_every_leave_one_out_rotation_refutes_both_canonical_shortcuts():
    expected = {"canonical_extent_only", "first_two_occurrences_only"}
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(10):
            lesson = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                source = gen.generate(20261012, start + offset, difficulty=difficulty)
                lesson.append((source, gen.rule_mirror(source)))

            for query_index in range(len(lesson)):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                for name in expected:
                    shortcut = gen.CANONICAL_SHORTCUTS[name]
                    assert any(shortcut(source) != output for source, output in demos), (
                        difficulty,
                        start,
                        query_index,
                        name,
                    )
