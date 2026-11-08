"""Observable geometry and reproducibility contracts for native episode inputs."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
HOME = ROOT / 'generators/49197f3c9375/workspace/parametric'
_spec = importlib.util.spec_from_file_location('_native_singleton_sampler_tests', HOME / 'sampler.py')
sampler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sampler)
selected, _, _ = load_selected_generator('49197f3c9375', root=ROOT)


def facts(grid):
    objs = selected._components(grid)
    counts = Counter(obj['signature'] for obj in objs)
    target = next(obj for obj in objs if counts[obj['signature']] == 1)
    return objs, counts, target


def hole_count(cells):
    cells = set(cells)
    maxr = max(r for r, _ in cells)
    maxc = max(c for _, c in cells)
    seen = {(-1, -1)}
    frontier = list(seen)
    while frontier:
        r, c = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if -1 <= p[0] <= maxr + 1 and -1 <= p[1] <= maxc + 1 and p not in cells and p not in seen:
                seen.add(p)
                frontier.append(p)
    return sum((r, c) not in cells and (r, c) not in seen
               for r in range(maxr + 1) for c in range(maxc + 1))


@pytest.mark.parametrize('seed', [0, 1, 17, 2**63 - 1])
def test_every_role_is_a_lawful_connected_d4_problem_with_size_confounds(seed):
    train, test = sampler.sample_inputs(seed, 6, 4)
    assert (len(train), len(test)) == (6, 4)
    for grid in train + test:
        assert type(grid) is list and 8 <= len(grid) <= 30
        assert 15 <= len(grid[0]) <= 30
        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
        assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
        objs, counts, target = facts(grid)
        assert len(objs) in (5, 7, 9)
        assert sorted(counts.values()) == [1] + [2] * ((len(objs) - 1) // 2)
        others = [obj for obj in objs if obj is not target]
        assert any(obj['size'] == target['size'] and
                   sorted((obj['height'], obj['width'])) == sorted((target['height'], target['width']))
                   for obj in others)
        # Every different object is separated by background even in monochrome scenes.
        for i, obj in enumerate(objs):
            occupied = set(obj['cells'])
            for other in objs[i + 1:]:
                assert all((r + dr, c + dc) not in occupied
                           for r, c in other['cells']
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_minimum_lesson_teaches_regions_selection_transforms_and_color_confounds(seed):
    train, _ = sampler.sample_inputs(seed)
    info = [facts(grid) for grid in train]
    assert [objs.index(target) for objs, _, target in info] == [2, 0, 4]
    assert [target['interior'] > 0 for _, _, target in info] == [True, True, False]
    assert all(target['size'] < target['height'] * target['width'] for _, _, target in info)
    assert hole_count(info[1][2]['local']) > 0
    assert any(obj is not info[1][2] and hole_count(obj['local']) > 0 for obj in info[1][0])
    assert any(obj is not info[0][2] and obj['interior'] > 0 for obj in info[0][0])
    assert len({obj['color'] for obj in info[0][0]}) == 5
    assert len({obj['color'] for obj in info[1][0]}) == 2
    assert len({obj['color'] for obj in info[2][0]}) == 1
    relations = set()
    for objs, counts, _ in info:
        for signature, count in counts.items():
            if count == 2:
                pair = [obj for obj in objs if obj['signature'] == signature]
                relations.add(selected._relation_kind(pair[0]['local'], pair[1]['local']))
    assert {'rotation_only', 'reflection_only'} <= relations


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_query_extremes_use_real_larger_geometries(seed):
    _, test = sampler.sample_inputs(seed)
    assert (len(test[0]), len(test[0][0])) == (8, 15)
    assert [len(facts(grid)[0]) for grid in test] == [5, 7, 9, 9]
    assert sum(facts(grid)[2]['interior'] > 0 for grid in test) >= 3
    maximum = test[3]
    assert (len(maximum), len(maximum[0])) == (30, 30)
    objs = facts(maximum)[0]
    assert all(obj['height'] == 8 and obj['width'] == 8 and obj['size'] >= 44 for obj in objs)
    occupied = [(r, c) for r, row in enumerate(maximum) for c, value in enumerate(row) if value]
    assert min(r for r, _ in occupied) <= 1 and max(r for r, _ in occupied) >= 28
    assert min(c for _, c in occupied) <= 1 and max(c for _, c in occupied) >= 28


def test_inputs_are_reproducible_fresh_prefix_stable_and_do_not_use_global_rng():
    state = random.getstate()
    full = sampler.sample_inputs(793, 6, 4)
    assert random.getstate() == state
    assert sampler.sample_inputs(793, 6, 4) == full
    assert sampler.sample_inputs(793, 3, 1) == (full[0][:3], full[1][:1])
    for demos in (3, 4, 5, 6):
        for queries in (1, 2, 3, 4):
            assert sampler.sample_inputs(793, demos, queries) == (full[0][:demos], full[1][:queries])
    changed = sampler.sample_inputs(793)
    changed[0][0][0][0] = 99
    assert sampler.sample_inputs(793)[0][0][0][0] != 99
    assert sampler.sample_inputs(794) != sampler.sample_inputs(793)


def _perimeter(obj):
    cells = set(obj['local'])
    return sum((r + dr, c + dc) not in cells for r, c in cells
               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))


def _orbit(obj):
    cells = obj['local']
    return len(selected._rotations(cells) | selected._rotations(selected._reflect_lr(cells)))


def _projection(obj):
    cells = obj['local']
    return tuple(sorted((tuple(sorted(Counter(r for r, c in cells).values())),
                         tuple(sorted(Counter(c for r, c in cells).values())))))


def _region(obj, mode):
    if mode != 'interior':
        return selected._render_object(obj, boundary_only=mode == 'boundary')
    cells = set(obj['local'])
    return [[obj['color'] if (r, c) in cells and
             all((r + dr, c + dc) in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
             else 0 for c in range(obj['width'])] for r in range(obj['height'])]


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
@pytest.mark.parametrize('mode', ['boundary', 'whole', 'interior'])
def test_three_demonstrations_refute_observed_scalar_and_symmetry_shortcuts(seed, mode):
    """Regress independent review's five demonstration-fit/query-conflict rivals."""
    train, _ = sampler.sample_inputs(seed)
    examples = [facts(grid) for grid in train]
    features = {'unique_perimeter': _perimeter,
                'unique_perimeter_and_interior': lambda obj: (_perimeter(obj), obj['interior']),
                'unique_d4_orbit_size': _orbit,
                'unique_projection_histogram': _projection}
    for name, feature in features.items():
        refuted = False
        for objs, _, target in examples:
            counts = Counter(feature(obj) for obj in objs)
            prediction = next((obj for obj in objs if counts[feature(obj)] == 1), objs[0])
            refuted |= _region(prediction, mode) != _region(target, mode)
        assert refuted, name
    assert any(_region(min(objs, key=_orbit), mode) != _region(target, mode)
               for objs, _, target in examples), 'most_symmetric'


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_interior_demonstrations_require_reflection_equivalence(seed):
    """Moving the ring first must not conceal a rotation-only grouping rival."""
    train, _ = sampler.sample_inputs(seed)
    refuted = False
    for grid in train:
        objs, _, target = facts(grid)
        key = lambda obj: min(selected._rotations(obj['local']))
        counts = Counter(key(obj) for obj in objs)
        prediction = next((obj for obj in objs if counts[key(obj)] == 1), objs[0])
        refuted |= _region(prediction, 'interior') != _region(target, 'interior')
    assert refuted


_QUERY_BASELINE = {
    0: ['0e09860410b7a46d12344428d1821defd5efafb5f5febf7ce58637164ae004d7',
        '678aa360f43b163072c52e2b5e79cecfcc5d7c2104d0a15a3839e64b60ee0e3d',
        'ee24e0ce41418f439b2dd11aa87da9f6fa042fdd68c1aa24be18bddc0bfccdb0',
        '571af843257d9df747452b7b5f2b23666713c2ea7b77ed5ffc19b0b5343f64d2'],
    17: ['b13484e891666e1a4fd88bac02acf18c3c69c2c03585031cdd3b91a13f8cdd8e',
         '0b616e6bdf6d37b76a50ffd94e129185e432c4fbd7372d31557a6a773e7b3bf7',
         'da20c3c75f93ee0b0369dfb163b08580a43cc1ab01fab12c18a22c64a33813b8',
         '70f7183ba48a7712e014817e130af771b10fa9bcdf3c09e3bd4bcede96108ac5'],
    2**63 - 1: ['9893109192fa5933b4fea94b509e82ca54172a61dc98b16c00d44921cb58e649',
               '7b41d0534d3525615d5b71bc3db0b1f279b8333ee09f166336b22dbb650cde85',
               '7d828aeb35a87148834a1c44f74328cde681d64702703d29566c97c0afd16816',
               'db8b6dffca6d4a57bc2eba4293e36d1a9622b815d5bdce0185213b31ece37766'],
}


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_teaching_repair_preserves_all_four_query_inputs(seed):
    _, queries = sampler.sample_inputs(seed)
    actual = [hashlib.sha256(json.dumps(grid, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
              for grid in queries]
    assert actual == _QUERY_BASELINE[seed]


@pytest.mark.parametrize('seed', [True, False, -1, 2**63, 1.0, '1', None])
def test_invalid_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        sampler.sample_inputs(seed)


@pytest.mark.parametrize('demos', [True, False, 2, 7, 3.0, '3', None])
def test_invalid_demo_count_is_rejected(demos):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, demos, 4)


@pytest.mark.parametrize('queries', [True, False, 0, 5, 1.0, '1', None])
def test_invalid_query_count_is_rejected(queries):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, 3, queries)
