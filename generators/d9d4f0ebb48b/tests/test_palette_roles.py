"""Regression tests for color-role leakage; run via workspace/review_checks.py."""
from __future__ import annotations

import copy
import importlib
from collections import deque

import pytest

GEN = importlib.import_module('puzzle_generators.per_puzzle.d9d4f0ebb48b.generator')


def legacy_palette_bbox(grid):
    """Wrong rule: bbox-fill components of colors 1..7; ignore 8 and 9."""
    out = copy.deepcopy(grid)
    seen = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not 1 <= value <= 7 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == value):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            for rr in range(min(x[0] for x in cells), max(x[0] for x in cells) + 1):
                for cc in range(min(x[1] for x in cells), max(x[1] for x in cells) + 1):
                    out[rr][cc] = value
    return out


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_l_profile_always_kills_legacy_palette_bbox(band):
    for seed in range(32):
        grid = GEN.generate(seed, 1, difficulty=band)
        assert legacy_palette_bbox(grid) != GEN.rule_mirror(grid), (band, seed)


@pytest.mark.parametrize('profile', GEN.SCENE_PROFILES)
def test_validator_is_closed_under_nonzero_color_permutations(profile):
    grid = GEN.generate(27, 0, scene_profile=profile)
    observed = GEN.observe_overrides(grid)
    output = GEN.rule_mirror(grid)
    for offset in range(1, 9):
        rename = lambda g: [[0 if v == 0 else 1 + (v - 1 + offset) % 9 for v in row] for row in g]
        recolored = rename(grid)
        assert GEN.self_check(recolored) == [], (profile, offset)
        assert GEN.observe_overrides(recolored) == observed
        assert GEN.rule_mirror(recolored) == rename(output)


@pytest.mark.parametrize('profile', ['l_distractor', 'multicolor_cross', 'boundary_repeat'])
def test_distractor_color_is_also_a_true_plus_color(profile):
    for seed in range(32):
        grid = GEN.generate(seed, 0, scene_profile=profile)
        analysis = GEN._analysis(grid)
        plus_colors = {t['color'] for t in analysis['triggers']}
        distractor_colors = {grid[r][c] for r, c in analysis['remainder']}
        assert plus_colors & distractor_colors, (profile, seed)


@pytest.mark.parametrize('profile', GEN.SCENE_PROFILES)
def test_every_nonzero_color_can_be_a_true_plus(profile):
    colors = set()
    for seed in range(96):
        grid = GEN.generate(seed, 0, scene_profile=profile)
        colors.update(t['color'] for t in GEN._trigger_centers(grid))
    assert colors == set(range(1, 10))


def test_palette_shortcut_is_part_of_the_semantic_contract():
    assert 'palette_gated_bbox' in GEN.SEMANTIC_RIVALS
    assert 'palette_gated_bbox' in GEN.WITNESS_RIVALS['shared_color_l_stays_unfilled']


def test_every_mutation_fixture_really_changes_the_original():
    original = GEN.generate(20260727, 1, difficulty='medium')
    for name, changed in GEN.mutation_fixtures():
        assert changed != original, name


def test_l_distractor_has_the_same_cell_count_as_a_plus():
    for seed in range(32):
        grid = GEN.generate(seed, 1)
        analysis = GEN._analysis(grid)
        assert len(analysis['remainder']) == 5
        assert all(len(t['plus_cells']) == 5 for t in analysis['triggers'])


def test_component_size_shortcut_is_part_of_the_contract():
    assert 'five_cell_bbox' in GEN.SEMANTIC_RIVALS
    assert 'five_cell_bbox' in GEN.WITNESS_RIVALS['five_cell_l_stays_unfilled']


def test_palette_witness_requires_shared_color_not_just_any_l():
    grid = GEN.generate(4, 1)
    analysis = GEN._analysis(grid)
    for trigger in analysis['triggers']:
        for r, c in trigger['plus_cells']:
            grid[r][c] = 2
    for r, c in analysis['remainder']:
        grid[r][c] = 9
    assert GEN.self_check(grid) == []
    assert not GEN.SEMANTIC_WITNESSES['shared_color_l_stays_unfilled'](grid)


def test_legacy_three_cell_l_is_still_accepted_but_not_a_five_cell_witness():
    grid = GEN.generate(5, 1)
    remainder = GEN._analysis(grid)['remainder']
    r0, c0, _, _ = GEN._bbox(remainder)
    color = grid[next(iter(remainder))[0]][next(iter(remainder))[1]]
    for r, c in remainder:
        grid[r][c] = 0
    for dr, dc in ((0, 0), (0, 1), (1, 0)):
        grid[r0+dr][c0+dc] = color
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES['l_distractor_stays_unfilled'](grid)
    assert not GEN.SEMANTIC_WITNESSES['five_cell_l_stays_unfilled'](grid)
