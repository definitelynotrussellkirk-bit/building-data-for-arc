"""Native completion composition: exact source, causal labels and count contracts."""
import importlib.util
import json
from pathlib import Path
import random

import pytest
from reviewer_support import find_root

HOME = find_root(__file__) / 'generators/a2d296c74658/workspace/parametric'


def family():
    source = HOME / 'prototype.py'
    assert source.exists(), 'native completion family is not implemented'
    spec = importlib.util.spec_from_file_location('completion_native_contract', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_new_yellow_cells_enable_the_second_stage():
    m = family()
    grid = [[7, 0, 7], [0, 0, 0], [7, 0, 7]]
    first = [[7, 0, 7], [4, 0, 4], [7, 0, 7]]
    cascade = [[7, 0, 7], [4, 2, 4], [7, 0, 7]]
    assert m.first_stage(grid) == first
    assert m.mirror(grid, {'completion_mode': 'vertical'}) == first
    assert m.mirror(grid, {'completion_mode': 'cascade'}) == cascade
    assert grid == [[7, 0, 7], [0, 0, 0], [7, 0, 7]]


def test_first_stage_can_remove_a_second_stage_zero_candidate():
    grid = [[0, 7, 0], [4, 0, 4], [0, 7, 0]]
    expected = [[0, 7, 0], [4, 4, 4], [0, 7, 0]]
    assert family().mirror(grid, {'completion_mode': 'cascade'}) == expected


def test_preexisting_and_mixed_yellow_anchors_are_eligible():
    m = family()
    assert m.mirror([[4, 0, 4]], {'completion_mode': 'cascade'}) == [[4, 2, 4]]
    grid = [[7, 0, 0], [0, 0, 4], [7, 0, 0]]
    assert m.mirror(grid, {'completion_mode': 'cascade'}) == [[7, 0, 0], [4, 2, 4], [7, 0, 0]]


def test_exact_canonical_program_and_strict_thin_grid_semantics():
    m = family()
    assert m.program({'completion_mode': 'vertical'}).encode() == (HOME / 'canonical.rkt').read_bytes()
    assert m.mirror([[7]], {'completion_mode': 'cascade'}) == [[7]]
    assert m.mirror([[7], [0], [7]], {'completion_mode': 'cascade'}) == [[7], [4], [7]]


@pytest.mark.parametrize('seed', [0, 1, 6, 12, 17, 31])
def test_two_demos_teach_crowded_gaps_long_lines_and_boundaries(seed):
    m = family()
    episode = m.generate(seed, {'completion_mode': 'cascade'}, 2, 4)
    crowd_a = crowd_b = boundary_a = boundary_b = long_a = long_b = many_a = many_b = False
    for pair in episode['train']:
        g = pair['input']; a = m.first_stage(g); h, w = len(g), len(g[0])
        ac = [(r, c) for r in range(1, h-1) for c in range(w)
              if g[r][c] == 0 and g[r-1][c] == g[r+1][c] == 7]
        bc = [(r, c) for r in range(h) for c in range(1, w-1)
              if a[r][c] == 0 and a[r][c-1] == a[r][c+1] == 4]
        def values(grid, r, c, offsets):
            return [grid[r+dr][c+dc] for dr, dc in offsets if 0 <= r+dr < h and 0 <= c+dc < w]
        box = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        crowd_a |= any(7 in values(g,r,c,[(0,-1),(0,1)]) and 7 in values(g,r,c,diagonal)
                       and any(v not in (0,4,7) for v in values(g,r,c,box)) for r,c in ac)
        crowd_b |= any(4 in values(a,r,c,[(-1,0),(1,0)]) and 4 in values(a,r,c,diagonal)
                       and any(v != 0 for v in values(a,r,c,[(0,-2),(0,2)]))
                       and any(v not in (0,4,7) for v in values(a,r,c,box)) for r,c in bc)
        boundary_a |= any(c in (0,w-1) and r in (1,h-2) for r,c in ac)
        boundary_b |= any(r in (0,h-1) and c in (1,w-2) for r,c in bc)
        long_a |= any(sum(c == col for r,c in ac) >= 5 for col in range(w))
        long_b |= any(sum(r == row for r,c in bc) >= 5 for row in range(h))
        many_a |= len(ac) > 32
        many_b |= len(bc) > 32
    assert all((crowd_a,crowd_b,boundary_a,boundary_b,long_a,long_b,many_a,many_b)), (
        seed,crowd_a,crowd_b,boundary_a,boundary_b,long_a,long_b,many_a,many_b)


@pytest.mark.parametrize('seed', [0, 1, 7, 17, 101, 2**63-1])
def test_count_prefixes_matched_settings_dense_large_case_and_no_rng_leak(seed):
    m = family()
    state = random.getstate()
    small = m.generate(seed, {'completion_mode': 'vertical'}, 2, 1)
    large = m.generate(seed, {'completion_mode': 'vertical'}, 6, 4)
    alternate = m.generate(seed, {'completion_mode': 'cascade'}, 3, 4)
    assert small['train'] == large['train'][:2]
    assert small['test'] == large['test'][:1]
    assert [x['input'] for x in alternate['train']] == [x['input'] for x in large['train'][:3]]
    assert [x['input'] for x in alternate['test']] == [x['input'] for x in large['test']]
    inputs = [json.dumps(x['input']) for x in large['train'] + large['test']]
    assert len(set(inputs)) == 10
    assert any(m.mirror(x['input'], {'completion_mode': 'cascade'}) != x['output'] for x in small['train'])
    stress = next(x['input'] for x in alternate['test'] if len(x['input']) == len(x['input'][0]) == 30)
    assert sum(v != 0 for row in stress for v in row) >= 300
    for r0, r1 in [(0, 15), (15, 30)]:
        for c0, c1 in [(0, 15), (15, 30)]:
            assert sum(stress[r][c] != 0 for r in range(r0, r1) for c in range(c0, c1)) >= 45
    info = m.analyze(stress)
    assert len(info['stage_a_cells']) >= 20
    assert len(info['stage_b_cells']) >= 10
    assert random.getstate() == state
    small['train'][0]['input'][0][0] = -9
    assert m.generate(seed, {'completion_mode': 'vertical'}, 2, 1)['train'] == large['train'][:2]


@pytest.mark.parametrize('seed,demos,queries,settings', [
    (-1, 3, 4, {'completion_mode': 'vertical'}), (True, 3, 4, {'completion_mode': 'vertical'}),
    (2**63, 3, 4, {'completion_mode': 'vertical'}), (0, 1, 4, {'completion_mode': 'vertical'}),
    (0, 7, 4, {'completion_mode': 'vertical'}), (0, 3, 0, {'completion_mode': 'vertical'}),
    (0, 3, 5, {'completion_mode': 'vertical'}), (0, True, 4, {'completion_mode': 'vertical'}),
    (0, 3, 4, {}), (0, 3, 4, {'completion_mode': 'bad'}),
    (0, 3, 4, {'completion_mode': 'vertical', 'other': 1})])
def test_invalid_requests_are_rejected(seed, demos, queries, settings):
    with pytest.raises((TypeError, ValueError)):
        family().generate(seed, settings, demos, queries)


@pytest.mark.parametrize('grid', [[], [[]], [[0], [0, 1]], [[True]], [[10]], ['070'], [[0] * 31]])
def test_malformed_grids_are_rejected(grid):
    with pytest.raises((TypeError, ValueError)):
        family().mirror(grid, {'completion_mode': 'cascade'})
