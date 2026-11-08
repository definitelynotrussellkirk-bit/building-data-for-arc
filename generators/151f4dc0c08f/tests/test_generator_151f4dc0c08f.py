"""Focused regression tests for the diagonal-teaching repair."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator("151f4dc0c08f", root=ROOT)


def _positions(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def _profile(grid):
    points = _positions(grid)
    row_col = diagonal_only = unrelated = 0
    for i, (r1, c1) in enumerate(points):
        for r2, c2 in points[i + 1 :]:
            same_row_col = r1 == r2 or c1 == c2
            diagonal = abs(r1 - r2) == abs(c1 - c2)
            if same_row_col:
                row_col += 1
            elif diagonal:
                diagonal_only += 1
            else:
                unrelated += 1
    return row_col, diagonal_only, unrelated


def test_reported_easy_lesson_window_now_contains_diagonal_evidence():
    # Both retained audits found this exact window could omit the diagonal clause.
    for index in (18, 19, 20, 21):
        grid = GEN.generate(1, index, difficulty="easy")
        _row_col, diagonal_only, unrelated = _profile(grid)
        assert diagonal_only >= 1, index
        if len(_positions(grid)) >= 3:
            assert unrelated >= 1, index


def test_normal_draws_always_teach_diagonal_and_nonrelation_when_possible():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 20261025):
            for index in range(24):
                grid = GEN.generate(seed, index, difficulty=difficulty)
                assert GEN.self_check(grid, difficulty=difficulty) == []
                _row_col, diagonal_only, unrelated = _profile(grid)
                assert diagonal_only >= 1, (difficulty, seed, index)
                if len(_positions(grid)) >= 3:
                    assert unrelated >= 1, (difficulty, seed, index)
                assert GEN.generate(seed, index, difficulty=difficulty) == grid


def test_degenerate_controls_remain_available():
    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(0, 0, texture=texture)
        assert GEN.self_check(grid) == []
