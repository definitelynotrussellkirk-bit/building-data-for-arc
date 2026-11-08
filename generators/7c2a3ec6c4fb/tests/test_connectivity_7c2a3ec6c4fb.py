"""Independent connectivity regressions; do not reuse generator segmentation."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
PATH = ROOT / 'generators/7c2a3ec6c4fb/generator.py'
SPEC = importlib.util.spec_from_file_location('connectivity_generator', PATH)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def independent_crops(grid, *, diagonal):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (not diagonal and abs(dr) + abs(dc) != 1):
                        continue
                    p = (r + dr, c + dc)
                    if p in unseen:
                        unseen.remove(p)
                        cells.add(p)
                        todo.append(p)
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        result.append(tuple(tuple(grid[r][c0:c1 + 1]) for r in range(r0, r1 + 1)))
    return result


def orthogonal_rival(grid):
    crops = independent_crops(grid, diagonal=False)
    counts = Counter(crops)
    return next((p for p in crops if counts[p] == 1), ())


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_answer_connectivity_not_an_unbroken_shortcut(difficulty):
    diagonal_answers = 0
    failures_of_rival = 0
    for i in range(240):
        grid = GEN.generate('connectivity-regression', i, difficulty=difficulty)
        crops = independent_crops(grid, diagonal=True)
        counts = Counter(crops)
        answer, = [p for p, n in counts.items() if n == 1]
        assert GEN.self_check(grid) == []
        assert answer == tuple(map(tuple, GEN.rule_mirror(grid)))
        diagonal_answers += len(independent_crops(answer, diagonal=False)) > 1
        failures_of_rival += orthogonal_rival(grid) != answer
    assert diagonal_answers >= 24, (difficulty, diagonal_answers, 240)
    assert failures_of_rival >= 24, (difficulty, failures_of_rival, 240)


def test_orthogonal_shortcut_has_executable_witness_contract():
    name = 'orthogonal_components'
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.LESSON_COMPETITORS
    assert GEN.WITNESS_RIVALS['diagonal_connectivity_counterexample'] == [name]
    for i in range(60):
        grid = GEN.generate('connectivity-witness', i)
        prediction = GEN.CANONICAL_SHORTCUTS[name](grid)
        assert tuple(map(tuple, prediction)) == orthogonal_rival(grid)
        if GEN.SEMANTIC_WITNESSES['diagonal_connectivity_counterexample'](grid):
            assert prediction != GEN.rule_mirror(grid)


def test_every_mask_is_tight_and_eight_connected():
    for mask in GEN._SHAPE_MASKS:
        assert len(independent_crops(mask, diagonal=True)) == 1, mask
        assert GEN._fills_bbox(mask), mask


@pytest.mark.parametrize('profile', ['color_swap', 'shape_shift', 'mixed_signature'])
def test_all_profiles_teach_diagonal_answers_without_losing_observability(profile):
    diagonal = 0
    for i in range(180):
        grid = GEN.generate('connectivity-profiles', i, pattern_profile=profile)
        assert GEN.observe_overrides(grid)['pattern_profile'] == profile
        diagonal += len(independent_crops(GEN.rule_mirror(grid), diagonal=False)) > 1
    assert diagonal >= 18, (profile, diagonal, 180)


def test_diagonal_answer_is_not_the_only_diagonal_object():
    # Otherwise a learner could simply select the diagonally connected object.
    hits = 0
    for i in range(240):
        grid = GEN.generate('diagonal-distractors', i)
        crops = independent_crops(grid, diagonal=True)
        counts = Counter(crops)
        answer, = [p for p, n in counts.items() if n == 1]
        if len(independent_crops(answer, diagonal=False)) > 1:
            hits += 1
            assert any(n == 2 and len(independent_crops(p, diagonal=False)) > 1
                       for p, n in counts.items()), crops
    assert hits >= 24


def test_rule_mirror_is_equivariant_to_grid_symmetry_and_nonzero_color_permutation():
    def rotate(grid):
        return [list(row) for row in zip(*grid[::-1])]

    def recolor(grid):
        return [[0 if v == 0 else 10 - v for v in row] for row in grid]

    for i in range(40):
        grid = GEN.generate('connectivity-metamorphic', i)
        expected = GEN.rule_mirror(grid)
        for reflected in (False, True):
            current = [row[::-1] for row in grid] if reflected else grid
            answer = [row[::-1] for row in expected] if reflected else expected
            for _ in range(4):
                assert GEN.self_check(current) == []
                assert GEN.rule_mirror(current) == answer
                assert GEN.rule_mirror(recolor(current)) == recolor(answer)
                current, answer = rotate(current), rotate(answer)


def test_independent_census_separates_diagonal_and_orthogonal_connectivity():
    path = PATH.parent / 'workspace/connectivity_census.py'
    spec = importlib.util.spec_from_file_location('connectivity_tool_test', path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    grid = [[1, 1, 0], [0, 0, 2]]
    assert tool.predict(grid, diagonal=True) == grid
    assert tool.predict(grid, diagonal=False) == [[1, 1]]
    for i in range(30):
        grid = GEN.generate('census-independent', i)
        assert tool.predict(grid, diagonal=True) == GEN.rule_mirror(grid)
        assert tuple(map(tuple, tool.predict(grid, diagonal=False))) == orthogonal_rival(grid)
