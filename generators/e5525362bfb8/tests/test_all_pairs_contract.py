"""Portable regressions for the bounded, all-pairs diagonal-plus curriculum."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = 'e5525362bfb8'
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / 'generators' / TASK / 'generator.py',
    ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py',
) if path.is_file())
SPEC = importlib.util.spec_from_file_location('all_pairs_task_under_test', SOURCE)
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)
LABELED = canonical_pairs(TASK, root=ROOT, labeled_only=True)
RECORD = next(json.loads(line) for line in canonical_path(ROOT).open()
              if json.loads(line).get('task_id') == TASK)
CANONICAL_INPUTS = [pair['input'] for split in ('train', 'test') for pair in RECORD[split]]
SCENES = {'pair': (2, 1), 'chain': (3, 3), 'bend': (3, 2), 'skipped': (3, 1), 'network': (5, 4)}
SCHEDULE = ('pair', 'network', 'network', 'chain', 'network', 'network',
            'bend', 'network', 'network', 'skipped', 'network', 'network')
CANONICAL_RIVALS = {'row_major_consecutive', 'gap_three_only', 'first_three_only', 'overwrite_green_arms', 'first_two_aligned_pairs'}
RIVALS = CANONICAL_RIVALS | {'first_two_only', 'positive_slope_only'}


def green_cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}


def centers(grid):
    green = green_cells(grid)
    return sorted((r, c) for r, c in green
                  if all((r + dr, c + dc) in green for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))))


def edges(grid):
    return [(a, b) for a, b in itertools.combinations(centers(grid), 2)
            if abs(a[0] - b[0]) == abs(a[1] - b[1]) > 1]


def expected_output(grid):
    """Independent cell-set formulation, checked against the labelled canonicals."""
    bridge = set()
    for (ar, ac), (br, bc) in edges(grid):
        sr, sc = (1 if br > ar else -1), (1 if bc > ac else -1)
        bridge.update((ar + k * sr, ac + k * sc) for k in range(1, abs(br - ar)))
    return [[2 if value == 0 and (r, c) in bridge else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


def footprint(cs):
    return {(r + dr, c + dc) for r, c in cs
            for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))}


def assert_generated_domain(grid):
    assert 8 <= len(grid) <= 24
    assert grid and 8 <= len(grid[0]) <= 24
    assert all(len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and value in {0, 3} for row in grid for value in row)
    cs = centers(grid)
    assert 2 <= len(cs) <= 5
    assert green_cells(grid) == footprint(cs)
    assert edges(grid)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('index', range(4))
def test_all_canonical_inputs_belong_to_the_validator_domain(index):
    assert gen.self_check(CANONICAL_INPUTS[index]) == []


def test_independent_rule_matches_every_labelled_canonical_pair():
    assert len(LABELED) == 3
    for pair in LABELED:
        assert expected_output(pair['input']) == pair['output']


def test_strict_domain_accepts_canonical_inputs():
    for grid in CANONICAL_INPUTS:
        verdict = gen.strict_canonical_like(grid)
        assert verdict is True or verdict == []


@pytest.mark.parametrize('scene', tuple(SCENES))
def test_constructive_scene_overrides_and_pixel_observation(scene):
    for height, width in ((8, 8), (8, 24), (24, 8)):
        kwargs = {'grid_h': height, 'grid_w': width, 'scene': scene}
        grid = gen.generate(29, 7, difficulty='medium', **kwargs)
        assert_generated_domain(grid)
        assert (len(centers(grid)), len(edges(grid))) == SCENES[scene]
        assert gen.observe_overrides(grid) == kwargs
        assert grid == gen.generate(29, 7, difficulty='medium', **kwargs)


@pytest.mark.parametrize('band', ('easy', 'medium', 'hard'))
def test_default_curriculum_has_canonical_profiles_and_rotation_witnesses(band):
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 12
    observed = []
    for index in range(15):
        grid = gen.generate(31, index, difficulty=band)
        assert_generated_domain(grid)
        scene = gen.observe_overrides(grid)['scene']
        assert scene == SCHEDULE[index % 12]
        if scene != 'network':
            side = 8 if scene == 'pair' else 11
            assert (len(grid), len(grid[0])) == (side, side)
        observed.append(scene)
    for start in range(12):
        window = observed[start:start + 4]
        assert window.count('network') >= 2
        for query_position in range(4):
            assert any(scene == 'network' for index, scene in enumerate(window) if index != query_position)


@pytest.mark.parametrize('overrides', (
    {'grid_h': 7}, {'grid_w': 25}, {'grid_h': True}, {'grid_w': 8.0},
    {'scene': 'invalid'}, {'scene': 1}, {'direction': 'down-right'}, {'unexpected_key': 2},
))
def test_invalid_and_unknown_overrides_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, difficulty='medium', **overrides)


def test_declared_rivals_have_correct_canonical_fit_claims():
    assert set(gen.AXES) == {'grid_h', 'grid_w', 'scene'}
    assert CANONICAL_RIVALS <= set(gen.CANONICAL_SHORTCUTS)
    assert not ({'first_two_only', 'positive_slope_only'} & set(gen.CANONICAL_SHORTCUTS))
    assert RIVALS <= set(gen.LESSON_COMPETITORS)
    assert RIVALS <= set(gen.SEMANTIC_RIVALS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in LABELED:
            original = copy.deepcopy(pair['input'])
            assert rival(pair['input']) == pair['output'], name
            assert pair['input'] == original, f'{name} mutated the input'


def test_compound_network_refutes_every_declared_lesson_rival_and_preserves_green_arms():
    grid = gen.generate(37, 1, difficulty='medium', grid_h=8, grid_w=8, scene='network')
    assert_generated_domain(grid)
    assert (len(centers(grid)), len(edges(grid))) == (5, 4)
    reference = expected_output(grid)
    original = copy.deepcopy(grid)
    assert reference != grid
    assert all(reference[r][c] == 3 for r, c in green_cells(grid))
    for name, rival in gen.LESSON_COMPETITORS.items():
        first = rival(grid)
        assert grid == original, f'{name} mutated the input'
        assert first == rival(grid), f'{name} is nondeterministic'
        assert first != reference, f'network fails to refute {name}'
    wrong = gen.LESSON_COMPETITORS['overwrite_green_arms'](grid)
    assert any(wrong[r][c] == 2 for r, c in green_cells(grid) - set(centers(grid)))


def test_network_refutes_an_independently_computed_two_aligned_pair_cap():
    grid = gen.generate(37, 1, difficulty='medium', grid_h=8, grid_w=8, scene='network')
    capped = copy.deepcopy(grid)
    for (ar, ac), (br, bc) in edges(grid)[:2]:
        sr, sc = (1 if br > ar else -1), (1 if bc > ac else -1)
        for k in range(1, abs(br - ar)):
            r, c = ar + k * sr, ac + k * sc
            if capped[r][c] == 0:
                capped[r][c] = 2
    assert capped != expected_output(grid), 'a two-aligned-pair cap still explains the network'


@pytest.mark.parametrize('mutation', ('missing_arm', 'orphan', 'wrong_color', 'bool', 'float', 'ragged', 'empty'))
def test_validator_rejects_malformed_or_incomplete_plus_inputs(mutation):
    grid = copy.deepcopy(CANONICAL_INPUTS[0])
    if mutation == 'missing_arm':
        grid[1][2] = 0
    elif mutation == 'orphan':
        grid[0][0] = 3
    elif mutation == 'wrong_color':
        grid[0][0] = 9
    elif mutation == 'bool':
        grid[0][0] = False
    elif mutation == 'float':
        grid[0][0] = 0.0
    elif mutation == 'ragged':
        grid[0].pop()
    else:
        grid = []
    verdict = gen.self_check(grid)
    assert isinstance(verdict, list) and verdict
