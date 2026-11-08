"""Source-review regressions for 2e0d26e28a50."""
from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "2e0d26e28a50"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator(TASK, root=ROOT)


def test_rule_mirror_matches_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_exact_dimension_and_motif_size_controls_include_30_by_30():
    grid = GEN.generate(
        101,
        4,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        motif_size=10,
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(cell == 2 for row in grid for cell in row) == 10
    assert GEN.self_check(grid, difficulty="hard") == []
    assert sum(cell == 8 for row in GEN.rule_mirror(grid) for cell in row) == 10


def test_default_draws_are_valid_varied_and_deterministic():
    state = random.getstate()
    signatures = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(71, index, difficulty=difficulty)
            second = GEN.generate(71, index, difficulty=difficulty)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first, difficulty=difficulty) == []
            info = GEN.analyze(first)
            signatures.add((info["motif_size"], info["motif_bbox"], info["marker"]))
    assert len(signatures) >= 12
    assert random.getstate() == state


def test_self_check_rejects_disconnected_reference_duplicate_marker_and_bad_stamp_bounds():
    valid = GEN.generate(9, 2, grid_h=12, grid_w=14, motif_size=5)

    disconnected = copy.deepcopy(valid)
    twos = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 2]
    r, c = twos[-1]
    disconnected[r][c] = 0
    disconnected[0][-1] = 2

    duplicate_marker = copy.deepcopy(valid)
    duplicate_marker[0][-1] = 1

    bad_bounds = copy.deepcopy(valid)
    for r, row in enumerate(bad_bounds):
        for c, value in enumerate(row):
            if value == 1:
                bad_bounds[r][c] = 0
    bad_bounds[0][0] = 1

    assert any("connected" in error for error in GEN.self_check(disconnected))
    assert any("marker" in error for error in GEN.self_check(duplicate_marker))
    assert any("bounds" in error for error in GEN.self_check(bad_bounds))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bogus": 1},
        {"difficulty": "extreme"},
        {"grid_h": 6},
        {"grid_w": 31},
        {"motif_size": 1},
        {"motif_size": True},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty=difficulty, **kwargs)
