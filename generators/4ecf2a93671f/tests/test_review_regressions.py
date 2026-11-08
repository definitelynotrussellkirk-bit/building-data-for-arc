"""Observable regressions: scalar contracts, canonical support and query ambiguity."""
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "4ecf2a93671f"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", False), ("seed", 1.0),
    ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False),
    ("sample_index", 1.0), ("sample_index", 1.75),
    ("sample_index", "1"), ("sample_index", -1),
    ("difficulty", True), ("difficulty", False),
    ("difficulty", 0), ("difficulty", 1.0),
    ("difficulty", "__invalid_difficulty__"),
    ("side", "3"), ("side", 3.0), ("side", 3.75),
    ("fg_color", True), ("fg_color", "1"),
    ("fg_color", 1.0), ("fg_color", 1.75),
    ("bg_count", "3"), ("bg_count", 3.0), ("bg_count", 3.75),
])
def test_invalid_scalars_are_rejected_before_rng_coercion(argument, value):
    options = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    options[argument] = value
    with pytest.raises(ValueError):
        GEN.generate(**options)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_default_canonical_anchors_cover_all_observed_zero_counts(difficulty):
    counts = Counter()
    for index in range(12):
        grid = GEN.generate(20261019, index, difficulty=difficulty)
        if len(grid) == 3:
            counts[sum(cell == 0 for row in grid for cell in row)] += 1
    assert set(counts) == {3, 4, 5}, counts
    assert min(counts.values()) >= 2, counts


def test_answer_equivalent_canonical_rival_does_not_reject_lawful_query():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    query = next(pair for pair in pairs if pair["split"] == "test")
    assert GEN.lesson_identifiable(demos, {"input": query["input"]}) == []


def test_same_demos_still_reject_size_rival_when_query_needs_generalization():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    query = GEN.generate(20261019, 2, side=4, fg_color=6, bg_count=5)
    reasons = GEN.lesson_identifiable(demos, {"input": query})
    assert any("fixed_side3_output" in reason for reason in reasons), reasons


def test_invalid_query_stays_a_validation_error():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    assert GEN.lesson_identifiable(demos, {"input": [[0]]})
