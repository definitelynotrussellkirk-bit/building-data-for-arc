"""The mixed-orientation contract is about objects, not global cell counts."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[3]
if (REPO / 'shared/runtime').is_dir():
    sys.path.insert(0, str(REPO / 'shared/runtime'))
from reviewer_support import find_root, load_selected_generator

GEN, _, _ = load_selected_generator('7eaf2d73ca39', root=find_root(__file__))


@pytest.mark.parametrize('texture', GEN.DEGENERATE_TEXTURES)
def test_self_check_rejects_builtin_degenerate_objects(texture):
    grid = GEN.generate(0, 0, texture=texture)
    assert GEN.self_check(grid), f'{texture} violates the straight mixed-object contract'


def test_self_check_rejects_blob_even_when_both_strips_are_present():
    grid = GEN.generate(0, 0)
    grid.extend([[0] * len(grid[0]) for _ in range(4)])
    for r, c in [(len(grid)-3, 1), (len(grid)-3, 2), (len(grid)-2, 1)]:
        grid[r][c] = 3
    assert any('straight' in error for error in GEN.self_check(grid))


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_self_check_accepts_existing_default_draws(difficulty):
    for seed in range(8):
        assert GEN.self_check(GEN.generate(seed, 0, difficulty=difficulty)) == []


def test_self_check_accepts_separate_lines_with_diagonal_contact():
    # Canonical objects use four-neighbor connectivity, so diagonal contact is lawful.
    grid = [[3, 3, 0, 0], [0, 0, 3, 0], [0, 0, 3, 0]]
    assert GEN.self_check(grid) == []


def test_self_check_does_not_reject_lawful_extra_singleton():
    grid = GEN.generate(0, 0)
    grid[0][0] = 3
    assert GEN.self_check(grid) == []
