"""Behavioral contract for the separate native maze-routing family."""
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import find_root

HOME = find_root(__file__) / 'generators/ad9405621c3d/workspace/parametric'


def family():
    p = HOME / 'prototype.py'
    assert p.is_file(), 'native routing family is not implemented'
    spec = importlib.util.spec_from_file_location('maze_native_contract', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def branch_scene():
    g = [[5] * 9 for _ in range(7)]
    for c in range(1, 8):
        g[1][c] = 0
    for r in range(2, 6):
        g[r][3] = 0
    g[5][4] = g[5][5] = 0
    g[1][1] = g[1][7] = 2
    return g


def test_farthest_waypoint_changes_the_painted_route():
    m = family()
    g = branch_scene()
    direct = [row[:] for row in g]
    for c in range(1, 8):
        direct[1][c] = 2
    via = [row[:] for row in direct]
    for r in range(2, 6):
        via[r][3] = 2
    via[5][4] = via[5][5] = 2
    assert m.mirror(g, {'route_mode': 'direct'}) == direct
    assert m.mirror(g, {'route_mode': 'via_farthest'}) == via
    assert m.analyze(g)['waypoint'] == [5, 5]
    assert g == branch_scene()


def test_exact_canonical_default():
    m = family()
    assert m.program({'route_mode': 'direct'}).encode() == (HOME / 'canonical.rkt').read_bytes()
    assert m.program({'route_mode': 'via_farthest'}).startswith('(rule! ')
    assert m.program({'route_mode': 'via_farthest'}) != m.program({'route_mode': 'direct'})


def test_two_walls_cannot_masquerade_as_the_canonical_endpoint_color():
    # The exact authority selects the first color occurring twice, including 5.
    # This broader mirror grammar used to mislabel the scene as a color-6 route.
    with pytest.raises(ValueError, match='wall'):
        family().mirror([[6, 0, 5], [0, 6, 5], [0, 0, 0]], {'route_mode': 'direct'})


@pytest.mark.parametrize('seed', [0, 1, 7, 17, 27, 123, 2**63 - 1])
def test_matched_inputs_count_prefixes_and_fresh_values(seed):
    m = family()
    state = random.getstate()
    small = m.generate(seed, {'route_mode': 'direct'}, 3, 1)
    big = m.generate(seed, {'route_mode': 'direct'}, 6, 4)
    alternate = m.generate(seed, {'route_mode': 'via_farthest'}, 3, 4)
    assert small['train'] == big['train'][:3]
    assert small['test'] == big['test'][:1]
    assert [p['input'] for p in alternate['train']] == [p['input'] for p in big['train'][:3]]
    assert [p['input'] for p in alternate['test']] == [p['input'] for p in big['test']]
    all_inputs = [json.dumps(p['input']) for p in big['train'] + big['test']]
    assert len(all_inputs) == len(set(all_inputs)) == 10
    assert any(m.mirror(p['input'], {'route_mode': 'via_farthest'}) != p['output'] for p in small['train'])
    assert any(len(p['input']) == len(p['input'][0]) == 30 for p in big['test'])
    large = next(p['input'] for p in big['test'] if len(p['input']) == len(p['input'][0]) == 30)
    assert sum(v != 5 for row in large for v in row) >= 350
    for r0, r1 in ((0, 15), (15, 30)):
        for c0, c1 in ((0, 15), (15, 30)):
            assert sum(large[r][c] != 5 for r in range(r0, r1) for c in range(c0, c1)) >= 60
    assert random.getstate() == state
    small['train'][0]['input'][0][0] = -99
    assert m.generate(seed, {'route_mode': 'direct'}, 3, 1) == {'train': big['train'][:3], 'test': big['test'][:1], 'program_solution': big['program_solution']}


@pytest.mark.parametrize('seed', [0, 1, 7, 17, 101])
def test_three_demonstrations_refute_executable_route_and_waypoint_rivals(seed):
    spec = importlib.util.spec_from_file_location('maze_native_rival_contract', HOME / 'rivals.py')
    rivals = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = rivals
    spec.loader.exec_module(rivals)
    m = family()
    for settings in m.SETTINGS:
        episode = m.generate(seed, settings, 3, 4)
        for rival in rivals.bank(settings):
            assert any(rival.apply(pair['input']) != pair['output'] for pair in episode['train']), (seed, settings, rival.name)


@pytest.mark.parametrize('seed,demos,queries,settings', [
    (-1, 3, 4, {'route_mode': 'direct'}), (True, 3, 4, {'route_mode': 'direct'}),
    (2**63, 3, 4, {'route_mode': 'direct'}), (0, 2, 4, {'route_mode': 'direct'}),
    (0, 7, 4, {'route_mode': 'direct'}), (0, 3, 0, {'route_mode': 'direct'}),
    (0, 3, 5, {'route_mode': 'direct'}), (0, True, 4, {'route_mode': 'direct'}),
    (0, 3, 4, {}), (0, 3, 4, {'route_mode': 'bad'}),
    (0, 3, 4, {'route_mode': 'direct', 'extra': 1})])
def test_invalid_requests_fail_loudly(seed, demos, queries, settings):
    with pytest.raises((TypeError, ValueError)):
        family().generate(seed, settings, demos, queries)
