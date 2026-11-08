from __future__ import annotations

import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "e282a664f807"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _pair_points(grid):
    counts = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                counts.setdefault(value, []).append((r, c))
    color = next(value for value, cells in counts.items() if len(cells) == 2)
    return color, counts[color]


def _slope(grid):
    _, (a, b) = _pair_points(grid)
    return "positive" if (a[0] - b[0]) * (a[1] - b[1]) > 0 else "negative"


def test_canonical_pairs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT, variant=0)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_two_consecutive_draws_cover_both_pair_slopes():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(8):
            grids = [
                GEN.generate(2820, start + offset, difficulty=difficulty)
                for offset in range(2)
            ]
            assert {_slope(grid) for grid in grids} == {"positive", "negative"}
            assert all(GEN.self_check(grid) == [] for grid in grids)


def test_declared_overrides_are_exact_and_observable_at_boundaries():
    cases = [
        {
            "grid_h": 5,
            "grid_w": 6,
            "box_height": 2,
            "box_width": 2,
            "pair_slope": "positive",
            "distractor_count": 0,
        },
        {
            "grid_h": 14,
            "grid_w": 16,
            "box_height": 8,
            "box_width": 8,
            "pair_slope": "negative",
            "distractor_count": 4,
        },
    ]
    for difficulty in (None, "easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(100 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("bad", [True, 2.0, "2"])
def test_integer_overrides_reject_coercion(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, grid_h=bad)


def test_unknown_override_and_unknown_difficulty_are_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis=2)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(321, 5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(321, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(321, 5, difficulty="hard") == second
