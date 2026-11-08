"""Catch metric shortcuts, lost teaching witnesses, and coerced exact controls."""

from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators/31e43af4bcfa/generator.py",
    ROOT / "puzzle_generators/per_puzzle/31e43af4bcfa/generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("inventory_curriculum_test", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def perimeter(cells):
    occupied = set(cells)
    return sum((r + dr, c + dc) not in occupied for r, c in occupied
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def metric_rivals(grid):
    def bbox_area(cells):
        return ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
                * (max(c for _, c in cells) - min(c for _, c in cells) + 1))

    return {
        name: gen._solve_with_key(grid, lambda cells, measure=measure:
                                  (measure(cells), *gen._reading_key(cells)))
        for name, measure in {
            "capped_area_three": lambda cells: min(len(cells), 3),
            "perimeter": perimeter,
            "bounding_box_area": bbox_area,
        }.items()
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("k", [2, 3, 4])
def test_rank_witness_distinguishes_area_from_other_geometric_measures(band, k):
    # Reverting the deliberate 3-versus-4 witness makes this fail even for K=2.
    grid = gen.generate(17, 0, difficulty=band, K=k, grid_h=5, grid_w=7)
    assert gen.self_check(grid) == []
    actual = gen.rule_mirror(grid)
    for name, prediction in metric_rivals(grid).items():
        assert prediction != actual, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_single_query_holdout_retains_the_declared_teaching_witnesses(band):
    # A period-three schedule with only three demos loses its sole row-tie
    # witness when that pair becomes the query. The original seed-0 case fails.
    for start in range(3):
        pairs = []
        for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(0, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for held_out, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, query) == [], (start, held_out)


def test_declared_canonical_shortcuts_really_fit_all_usable_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("axis,value", [
    ("K", 2.9), ("grid_h", 5.9), ("grid_w", 7.9),
    ("K", "3"), ("grid_h", "5"), ("grid_w", "7"),
    ("K", True), ("grid_h", True), ("grid_w", True),
])
def test_exact_integer_axes_reject_coercion(axis, value):
    with pytest.raises(TypeError, match="integer"):
        gen.generate(11, 0, **{axis: value})


def test_hand_checked_square_and_triomino_reference_fixture():
    # Expected cells are derived directly from the stated rank/crop/pack rule.
    grid = [
        [9, 2, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
    ]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == [[9, 9, 0, 2, 2], [9, 0, 0, 2, 2]]
    for prediction in metric_rivals(grid).values():
        assert prediction == [[9, 9, 0, 2, 2], [9, 9, 0, 2, 0]]
