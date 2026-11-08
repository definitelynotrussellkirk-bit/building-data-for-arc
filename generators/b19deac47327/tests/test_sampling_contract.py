"""Regressions for strict call arguments and useful default shape support."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("b19deac47327", root=find_root(__file__))


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_a_literal_integer(value):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(value, 0, difficulty="easy")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_sample_index_requires_a_literal_integer(value):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, value, difficulty="hard")


def test_sample_index_rejects_negative_schedule_positions():
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, -1)


def test_integer_seed_domain_and_default_shapes_remain_deterministic():
    for seed in (-7, 0, 991):
        for index in range(4):
            first = GEN.generate(seed, index, difficulty="medium")
            assert first == GEN.generate(seed, index, difficulty="medium")
            assert GEN.self_check(first) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_tie_curriculum_varies_shape_without_losing_teaching_witnesses(difficulty):
    heights, widths, shapes = set(), set(), set()
    canonical_profiles = {(14, 10, 4), (12, 13, 4), (12, 10, 4), (16, 18, 4)}
    for seed in range(16):
        pairs = []
        for index in range(4):
            grid = GEN.generate(seed, index, difficulty=difficulty)
            height, width = len(grid), len(grid[0])
            heights.add(height)
            widths.add(width)
            shapes.add((height, width))
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            if index == 0:
                assert (height, width) == (12, 10)
            elif index == 2:
                assert (height, width) == (12, 13)
            else:
                assert GEN.SEMANTIC_WITNESSES["tie_break_to_first_discriminator"](grid)
                assert GEN.SEMANTIC_WITNESSES["unseen_edge_discriminator"](grid)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert sum((len(p["input"]), len(p["input"][0]), 4) in canonical_profiles
                   for p in pairs) >= 2
        for held_out, query in enumerate(pairs):
            demos = [p for i, p in enumerate(pairs) if i != held_out]
            assert GEN.lesson_identifiable(demos, query) == []
    assert heights == {12, 13, 14, 15, 16}
    assert min(widths) == 10 and max(widths) == 18
    assert len(shapes) >= 12
