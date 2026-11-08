"""Regressions added by review-a96e0d695b05f8c2."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "5a85abd1e231"
ROOT = find_root(__file__)
GEN, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize(
    ("seed", "sample_index", "message"),
    [
        (True, 0, "seed"),
        (False, 0, "seed"),
        (1.0, 0, "seed"),
        (1.75, 0, "seed"),
        ("1", 0, "seed"),
        (1, True, "sample_index"),
        (1, False, "sample_index"),
        (1, 1.0, "sample_index"),
        (1, 1.75, "sample_index"),
        (1, "1", "sample_index"),
        (1, -1, "sample_index"),
    ],
)
def test_invalid_seed_and_sample_index_scalars_fail_closed(seed, sample_index, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        GEN.generate(seed, sample_index, difficulty="easy")


def test_noncanonical_rivals_are_not_declared_as_canonical_shortcuts() -> None:
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_query_rotation_of_the_scheduled_four_pair_lesson_is_identifiable(band: str) -> None:
    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(8080 + sample_index, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

    for query_index in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, pairs[query_index]) == [], (band, query_index)
