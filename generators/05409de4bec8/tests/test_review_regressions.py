"""Portable regressions for review-7fe75b0957073e34.

The inherited ``test_generator_05409de4bec8.py`` fixture is frozen by the
assignment.  New coverage therefore uses only the public reviewer helpers and
lives in this separate file.
"""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "05409de4bec8"
ROOT = find_root(__file__)
G, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, -1, 1.0, 1.75, "1"])
def test_seed_requires_a_nonnegative_plain_integer(bad_seed: object) -> None:
    with pytest.raises((TypeError, ValueError), match="seed"):
        G.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, -1, 1.0, 1.75, "1"])
def test_sample_index_requires_a_nonnegative_plain_integer(bad_index: object) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        G.generate(0, bad_index)


def test_semantic_rivals_are_real_and_canonical_shortcut_fits_all_labels() -> None:
    assert G.VERSION == "5.0.0"
    assert G.RULE_HASH == "dfbf6efa8173"
    assert set(G.SEMANTIC_RIVALS) == {
        "all_pair_lines",
        "single_pair_per_axis",
    }

    shortcut = G.CANONICAL_SHORTCUTS["single_pair_per_axis"]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert shortcut(pair["input"]) == pair["output"]

    rectangle = G.generate(431, 0, difficulty="medium")
    multi_pair = G.generate(431, 1, difficulty="medium")
    assert G._analyze(rectangle)["facts"]["rectangle"]
    assert G.SEMANTIC_WITNESSES["rectangle_long_axis_exception"](rectangle)
    assert G.SEMANTIC_WITNESSES["multiple_parallel_pair_lines"](multi_pair)
    assert G.rule_mirror(rectangle) != G.SEMANTIC_RIVALS["all_pair_lines"](rectangle)
    assert G.rule_mirror(multi_pair) != shortcut(multi_pair)


def test_five_slot_curriculum_is_safe_under_every_query_rotation() -> None:
    assert G.LESSON_SCHEDULE_PERIOD == 5
    assert len(G.SCHEDULE_PROFILES) == 5

    for difficulty in ("easy", "medium", "hard"):
        for start in range(G.LESSON_SCHEDULE_PERIOD):
            pairs = []
            profiles = []
            for offset in range(G.LESSON_SCHEDULE_PERIOD):
                sample_index = start + offset
                grid = G.generate(8000 + start, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": G.rule_mirror(grid)})
                profiles.append(G.schedule_profile(8000 + start, sample_index, difficulty))

            assert set(profiles) == set(G.SCHEDULE_PROFILES)
            assert sum(
                G.SEMANTIC_WITNESSES["rectangle_long_axis_exception"](pair["input"])
                for pair in pairs
            ) >= 2
            assert sum(
                G.SEMANTIC_WITNESSES["multiple_parallel_pair_lines"](pair["input"])
                for pair in pairs
            ) >= 2

            for query_index, query in enumerate(pairs):
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                assert G.lesson_identifiable(demos, query) == []
