from __future__ import annotations

from puzzle_generators.per_puzzle.e1516c24afbd import generator as gen
from reviewer_support import canonical_pairs, find_root


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_profile_only_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert gen._canonical_profile_only(pair["input"]) == pair["output"]


def test_default_generator_emits_an_exact_counterexample_to_profile_shortcut():
    grid = gen.generate(5000, 1, difficulty="easy")
    assert (len(grid) // 2, len(grid[0])) == (5, 3)
    intended = gen.rule_mirror(grid)
    shortcut = gen._canonical_profile_only(grid)
    assert intended == [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 2, 0],
        [0, 0, 2],
    ]
    assert shortcut == [[0, 0, 0] for _ in range(5)]
    assert shortcut != intended


def test_lesson_hook_rejects_canonical_only_demos_when_query_is_noncanonical():
    canonical = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    demos = canonical[:3]
    query = _pair(gen.generate(5000, 1, difficulty="easy"))
    reasons = gen.lesson_identifiable(demos, query)
    assert any("canonical-profile-only" in reason for reason in reasons)


def test_fully_default_odd_slots_are_noncanonical_shape_witnesses():
    for band in ("easy", "medium", "hard"):
        for offset in range(24):
            sample_index = 2 * offset + 1
            grid = gen.generate(30_000 + offset, sample_index, difficulty=band)
            assert (len(grid) // 2, len(grid[0])) != (3, 3), (
                band,
                30_000 + offset,
                sample_index,
            )
