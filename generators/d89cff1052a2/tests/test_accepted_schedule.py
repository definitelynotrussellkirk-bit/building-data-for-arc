"""Teaching witnesses must survive the production sampler's duplicate filter."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("d89cff1052a2", root=find_root(__file__))


def _accepted_inputs(seed, start, difficulty):
    """Mirror only the documented duplicate filter, not the generator schedule.

    The canonical transformation is injective because it includes the original
    grid. Input equality therefore coincides with labelled-pair equality here.
    The Racket-backed public worker reproduction is retained with the review.
    """
    seen = set()
    accepted = []
    for index in range(start, start + 20):
        grid = GEN.generate(seed, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        key = tuple(tuple(row) for row in grid)
        if key in seen:
            continue
        seen.add(key)
        accepted.append((index, grid))
        if len(accepted) == 4:
            return accepted
    pytest.fail("could not assemble four distinct lawful pairs in 20 draws")


def _assert_rotation_teaches_full_height(accepted):
    for query_position in range(4):
        demonstrations = [grid for pos, (_, grid) in enumerate(accepted) if pos != query_position]
        # Full-height reflection and the canonical-consistent fixed-three-row
        # shortcut differ exactly when at least one demonstration is not 3 rows.
        assert any(len(grid) != 3 for grid in demonstrations), {
            "accepted_indices": [index for index, _ in accepted],
            "accepted_heights": [len(grid) for _, grid in accepted],
            "query_position": query_position,
        }


def test_seed_43514_keeps_a_full_height_witness_after_duplicate_rejection():
    """v2.0.1 drops repeated index 3 and accepts [0, 1, 2, 4]."""
    _assert_rotation_teaches_full_height(_accepted_inputs(43514, 0, "easy"))


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_accepted_lessons_keep_two_distinct_broad_witnesses(difficulty, start):
    for seed in (0, 1, 7, 27, 43514, 104729):
        _assert_rotation_teaches_full_height(_accepted_inputs(seed, start, difficulty))


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_any_four_raw_slots_have_two_distinct_non_three_row_inputs(difficulty):
    """This property remains true after duplicate removal, regardless of seeds."""
    for seed in (0, 1, 7, 27, 43514, 104729):
        for start in range(8):
            grids = [GEN.generate(seed, index, difficulty=difficulty)
                     for index in range(start, start + 4)]
            broad = {tuple(tuple(row) for row in grid) for grid in grids if len(grid) != 3}
            assert len(broad) >= 2, (difficulty, seed, start)
