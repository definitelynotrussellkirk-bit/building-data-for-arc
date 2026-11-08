from __future__ import annotations

import importlib

import pytest

GEN = importlib.import_module("puzzle_generators.per_puzzle.49c16a3506ab.generator")


def _ordered_scatter_counts(grid):
    blocks = GEN._find_blocks(grid)
    pair = GEN._pair_name(value[0] for value in blocks.values())
    colors_by_corner = {corner: color for color, (corner, _) in blocks.items()}
    scatter = GEN._scatter_by_color(grid, blocks)
    return tuple(len(scatter[colors_by_corner[corner]]) for corner in GEN._pair_corners(pair))


@pytest.mark.parametrize(
    ("relation", "expected_counts"),
    [
        ("equal", (6, 6)),
        ("first_sparse", (4, 6)),
        ("second_sparse", (6, 4)),
    ],
)
def test_scatter_relation_override_is_exactly_observable(relation, expected_counts):
    grid = GEN.generate(
        501,
        17,
        difficulty="hard",
        grid_h=15,
        grid_w=15,
        corner_pair="main",
        scatter_count=6,
        scatter_relation=relation,
        branch_bias="diagonal",
    )
    assert _ordered_scatter_counts(grid) == expected_counts
    assert GEN.observe_overrides(grid)["scatter_relation"] == relation
    assert GEN.observe_overrides(grid)["scatter_count"] == 6


def test_every_four_consecutive_default_draws_cover_both_corner_pairs():
    for seed in range(12):
        for start in range(8):
            observed = {
                GEN.observe_overrides(
                    GEN.generate(80_000 + seed, start + offset, difficulty="medium")
                )["corner_pair"]
                for offset in range(4)
            }
            assert observed == {"main", "anti"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_draw_refutes_nearest_anchor_shortcut(band):
    for index in range(80):
        grid = GEN.generate(190_000 + index, index * 13 + 5, difficulty=band)
        assert GEN._nearest_anchor(grid) != GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["color_binding"](grid)


def test_four_pair_lessons_refute_canonical_main_only_in_every_rotation():
    assert "canonical_main_only" in GEN.LESSON_COMPETITORS
    for seed in range(20):
        pairs = []
        for index in range(4):
            grid = GEN.generate(260_000 + seed, index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []
