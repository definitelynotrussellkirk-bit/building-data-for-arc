"""Focused regressions for the row-major nearest-square tie lesson."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0bd65c18b34c"
ROOT = find_root(__file__)
generator, _source_path, _source_digest = load_selected_generator(
    TASK_ID,
    root=ROOT,
)
RIVAL = "topmost_then_rightmost"
WITNESS = "row_major_same_row_tie"


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = generator.generate(
        seed,
        sample_index,
        difficulty=difficulty,
    )
    return {"input": grid, "output": generator.rule_mirror(grid)}


def test_balanced_profile_contains_a_distinguishing_same_row_tie():
    for seed in range(12):
        grid = generator.generate(
            seed,
            10_000 + seed,
            difficulty="hard",
            scene_profile="large_four_balanced",
        )
        assert generator.self_check(grid) == []
        assert generator.SEMANTIC_WITNESSES[WITNESS](grid)
        canonical = generator.rule_mirror(grid)
        rival = generator.SEMANTIC_RIVALS[RIVAL](grid)
        assert rival != canonical

        _coerced, facts, errors = generator._scene_analysis(grid)
        assert errors == []
        assert any(
            info["tie_count"] == 2
            and len({facts["squares"][index][0]
                     for index in info["tied_indices"]}) == 1
            and facts["squares"][info["nearest_index"]][0]
            <= row
            <= facts["squares"][info["nearest_index"]][0] + 1
            for (row, _col), info in zip(
                facts["blues"],
                facts["dot_infos"],
            )
        )


def test_declared_rival_fits_every_labeled_canonical_pair():
    rival = generator.SEMANTIC_RIVALS[RIVAL]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert rival(pair["input"]) == pair["output"]


def test_every_three_demo_window_refutes_the_canonical_fitting_rival():
    assert generator.EXAMPLES_NEEDED == 3
    assert generator.LESSON_SCHEDULE_PERIOD == 2
    assert set(generator.SCHEDULE_PROFILES) == {"ordinary", "tie_break"}

    for difficulty in ("easy", "medium", "hard"):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            demos = [
                _pair(7331 + start, start + offset, difficulty)
                for offset in range(generator.EXAMPLES_NEEDED)
            ]
            query = _pair(
                7331 + start,
                start + generator.EXAMPLES_NEEDED,
                difficulty,
            )
            assert any(
                generator.SEMANTIC_WITNESSES[WITNESS](pair["input"])
                for pair in demos
            )
            assert any(
                generator.SEMANTIC_RIVALS[RIVAL](pair["input"])
                != pair["output"]
                for pair in demos
            )
            assert generator.lesson_identifiable(demos, query) == []


def test_every_four_pair_window_remains_identifiable_under_query_rotation():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(9917 + start, start + offset, difficulty)
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                demos = [
                    pair
                    for index, pair in enumerate(pairs)
                    if index != query_index
                ]
                assert any(
                    generator.SEMANTIC_WITNESSES[WITNESS](pair["input"])
                    for pair in demos
                )
                assert any(
                    generator.SEMANTIC_RIVALS[RIVAL](pair["input"])
                    != pair["output"]
                    for pair in demos
                )
                assert generator.lesson_identifiable(demos, query) == []


def test_explicit_profile_override_takes_precedence_over_lesson_schedule():
    grid = generator.generate(
        17,
        1,
        difficulty="hard",
        scene_profile="compact_two",
    )
    assert generator.schedule_profile(17, 1, "hard") == "tie_break"
    assert generator.observe_overrides(grid) == {"scene_profile": "compact_two"}


@pytest.mark.parametrize("bad_seed", [True, 1.0, "1", None])
def test_schedule_profile_rejects_noninteger_seed(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        generator.schedule_profile(bad_seed, 0, "easy")
