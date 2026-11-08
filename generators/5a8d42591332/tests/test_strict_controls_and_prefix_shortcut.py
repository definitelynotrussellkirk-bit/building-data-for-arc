"""Regressions for strict controls and canonical-mask shortcut coverage."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "5a8d42591332", root=ROOT
)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index, difficulty="easy")


@pytest.mark.parametrize("min_count", [True, 1.0, "1"])
def test_min_count_override_requires_a_literal_integer(min_count):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty="easy", min_count=min_count)


def test_generated_examples_cover_every_available_count_value():
    """The non-compact layouts must compare multiple non-full header counts."""
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for sample_index in range(12):
                grid = gen.generate(seed, sample_index, difficulty=band)
                facts = gen._analyze(grid)
                assert set(facts["top_counts"] + facts["left_counts"]) == set(
                    range(facts["min_count"], 5)
                )


def test_row_major_prefix_count_is_a_canonical_fitting_declared_shortcut():
    name = "row_major_prefix_count"
    assert name in gen.CANONICAL_SHORTCUTS
    assert name in gen.LESSON_COMPETITORS
    shortcut = gen.CANONICAL_SHORTCUTS[name]
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
        assert shortcut(pair["input"]) == pair["output"]


def test_every_three_example_window_refutes_row_major_prefix_count():
    shortcut = gen.LESSON_COMPETITORS["row_major_prefix_count"]
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(12):
                demos = [
                    gen.generate(seed, start + offset, difficulty=band)
                    for offset in range(gen.EXAMPLES_NEEDED)
                ]
                assert any(
                    shortcut(grid) != gen.solve_python(grid) for grid in demos
                ), (band, seed, start)


def test_every_noncompact_default_example_refutes_row_major_prefix_count():
    """Either noncompact texture must independently teach true cell counts."""
    shortcut = gen.LESSON_COMPETITORS["row_major_prefix_count"]
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in range(18):
                grid = gen.generate(seed, sample_index, difficulty=band)
                layout = gen.observe_overrides(grid)["header_layout"]
                if layout != "compact":
                    assert shortcut(grid) != gen.solve_python(grid), (
                        band,
                        seed,
                        sample_index,
                        layout,
                    )


def test_census_regression_every_held_out_query_keeps_a_prefix_witness():
    """Regression for the first ambiguous rotation in the 300-lesson census."""
    shortcut = gen.LESSON_COMPETITORS["row_major_prefix_count"]
    grids = [
        gen.generate(699_585_569, sample_index, difficulty="easy")
        for sample_index in range(1, 5)
    ]
    for query_index in range(4):
        demos = [grid for index, grid in enumerate(grids) if index != query_index]
        assert any(
            shortcut(grid) != gen.solve_python(grid) for grid in demos
        ), query_index
