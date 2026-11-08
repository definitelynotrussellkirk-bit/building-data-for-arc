"""Independent geometry regressions for the three-demo dihedral curriculum."""
from collections import Counter, defaultdict
import importlib.util
import os
from itertools import product
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
SOURCE = Path(os.environ.get('CURRICULUM_TEST_SOURCE', ROOT / 'generators/c39bef185e7e/generator.py'))
if not SOURCE.exists():
    SOURCE = ROOT / 'puzzle_generators/c39bef185e7e.py'
spec = importlib.util.spec_from_file_location('curriculum_generator', SOURCE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def green_objects(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 3}
    objects = []
    while remaining:
        todo = [remaining.pop()]
        cells = set(todo)
        while todo:
            r, c = todo.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    todo.append(neighbor)
        objects.append(cells)
    return objects


def shape_key(cells):
    """Enumerate signed coordinate permutations, independently of generator helpers."""
    keys = []
    for swap, sr, sc in product((False, True), (-1, 1), (-1, 1)):
        transformed = [(sr * (c if swap else r), sc * (r if swap else c)) for r, c in cells]
        mr, mc = min(r for r, c in transformed), min(c for r, c in transformed)
        keys.append(tuple(sorted((r-mr, c-mc) for r, c in transformed)))
    return min(keys)


def oracle(grid):
    groups = defaultdict(list)
    for cells in green_objects(grid):
        groups[shape_key(cells)].append(cells)
    assert sorted(map(len, groups.values())) in ([1, 2], [1, 3], [1, 4])
    unique = next(objects[0] for objects in groups.values() if len(objects) == 1)
    common = next(objects for objects in groups.values() if len(objects) > 1)
    output = [row[:] for row in grid]
    for r, c in unique:
        output[r][c] = 8
    return output, common, unique


def measurement_rival(grid, measure):
    objects = green_objects(grid)
    counts = Counter(measure(cells) for cells in objects)
    output = [row[:] for row in grid]
    for cells in objects:
        if counts[measure(cells)] == 1:
            for r, c in cells:
                output[r][c] = 8
    return output


def bbox_area(cells):
    return (max(r for r, c in cells)-min(r for r, c in cells)+1) * (max(c for r, c in cells)-min(c for r, c in cells)+1)


def rotation_key(cells):
    keys = []
    for k in range(4):
        transformed = []
        for r, c in cells:
            for _ in range(k):
                r, c = -c, r
            transformed.append((r, c))
        mr, mc = min(r for r, c in transformed), min(c for r, c in transformed)
        keys.append(tuple(sorted((r-mr, c-mc) for r, c in transformed)))
    return min(keys)


def is_chiral(cells):
    return rotation_key(cells) != rotation_key({(r, -c) for r, c in cells})


def endpoint_count(cells):
    return sum(sum(neighbor in cells for neighbor in ((r-1,c), (r+1,c), (r,c-1), (r,c+1))) == 1 for r,c in cells)


def test_every_default_window_has_two_joint_scalar_witnesses():
    matched = []
    for i in range(243):
        _, common, unique = oracle(g.generate(17, i, difficulty='medium'))
        matched.append((len(unique), bbox_area(unique), is_chiral(unique), endpoint_count(unique)) ==
                       (len(common[0]), bbox_area(common[0]), is_chiral(common[0]), endpoint_count(common[0])))
    assert [(i, matched[i:i+4]) for i in range(240) if sum(matched[i:i+4]) < 2] == []


def independent_observations(grid):
    _, common, unique = oracle(grid)
    h, w = len(grid), len(grid[0])
    r, c, color = next((r, c, color) for r, row in enumerate(grid) for c, color in enumerate(row) if color not in (0, 3))
    quadrant = ('top' if sum(r for r, c in unique)/len(unique) < h/2 else 'bottom') + '_' + ('left' if sum(c for r, c in unique)/len(unique) < w/2 else 'right')
    return {'grid_h': h, 'grid_w': w, 'common_count': len(common), 'motif_size': len(common[0]),
            'size_relation': 'equal' if len(unique) == len(common[0]) else 'different',
            'unique_quadrant': quadrant, 'marker_color': color,
            'marker_corner': ('top' if r == 0 else 'bottom') + '_' + ('left' if c == 0 else 'right')}


def declarations():
    return {f'{attribute}:{name}': fn for attribute in ('LESSON_COMPETITORS', 'CANONICAL_SHORTCUTS')
            for name, fn in getattr(g, attribute).items()}


def test_literal_reflection_fixture_has_only_one_outlier():
    # Three Ls, including a reflected copy, and one O: literal expected O cells.
    grid = [[0] * 12 for _ in range(10)]
    for cells in ({(1,0),(2,0),(3,0),(3,1)}, {(1,8),(2,8),(3,8),(3,7)},
                  {(6,0),(6,1),(6,2),(7,0)}, {(6,8),(6,9),(7,8),(7,9)}):
        for r, c in cells:
            grid[r][c] = 3
    grid[0][0] = 4
    expected = [row[:] for row in grid]
    for r, c in {(6,8),(6,9),(7,8),(7,9)}:
        expected[r][c] = 8
    assert oracle(grid)[0] == expected
    assert g.self_check(grid) == []
    assert g.rule_mirror(grid) == expected


def test_all_usable_canonical_pairs_validate_and_match_labels():
    pairs = canonical_pairs(g.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert g.self_check(pair['input']) == []
        assert oracle(pair['input'])[0] == pair['output']
        assert g.rule_mirror(pair['input']) == pair['output']
    assert g.CANONICAL_SHORTCUTS
    for rival in g.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair['input']) == pair['output'] for pair in pairs)


@pytest.mark.parametrize('measure', [len, bbox_area], ids=['cell_count', 'bbox_area'])
def test_every_cyclic_window_retains_two_measurement_witnesses(measure):
    # Two refuting pairs prevent holding out the only discriminator.
    pairs = [({'input': grid, 'output': oracle(grid)[0]}) for index in range(243)
             for grid in [g.generate(17, index, difficulty='medium')]]
    failures = []
    for start in range(240):
        window = pairs[start:start+4]
        witness_count = sum(measurement_rival(p['input'], measure) != p['output'] for p in window)
        if witness_count < 2:
            failures.append((start, witness_count))
    assert failures == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_all_default_rotations_eliminate_current_declared_competitors(band):
    assert g.EXAMPLES_NEEDED == 3
    pairs = [{'input': grid, 'output': oracle(grid)[0]} for index in range(243)
             for grid in [g.generate(17, index, difficulty=band)]]
    failures = []
    for start in range(240):
        window = pairs[start:start+4]
        for qi, query in enumerate(window):
            demos = [p for i, p in enumerate(window) if i != qi]
            for name, rival in declarations().items():
                if all(rival(p['input']) == p['output'] for p in demos) and rival(query['input']) != query['output']:
                    failures.append((start, qi, name))
            reasons = g.lesson_identifiable(demos, query)
            if reasons:
                failures.append((start, qi, reasons))
    assert failures == []


def test_default_joint_schedule_has_all_quadrant_relation_count_combinations():
    observations = [independent_observations(g.generate(17, i)) for i in range(240)]
    expected = set(product(('top_left', 'top_right', 'bottom_left', 'bottom_right'),
                           ('equal', 'different'), (2, 3, 4)))
    actual = {(o['unique_quadrant'], o['size_relation'], o['common_count']) for o in observations}
    assert actual == expected
    assert g.SCHEDULE_PERIOD == 240
    assert all(g.schedule_profile(17, i) == g.schedule_profile(17, i+240) for i in range(240))
    assert all(g.schedule_profile(17, i) in g.SCHEDULE_PROFILES for i in range(240))


def test_exact_size_relation_is_honored_jointly_with_existing_controls():
    assert 'size_relation' in g.AXES
    for i, (size, relation, quadrant, count) in enumerate(product((3, 4, 5), ('equal', 'different'),
            ('top_left', 'top_right', 'bottom_left', 'bottom_right'), (2, 3, 4))):
        controls = {'grid_h': 10 + i % 2, 'grid_w': 12 + (i // 2) % 2,
                    'motif_size': size, 'size_relation': relation, 'unique_quadrant': quadrant,
                    'common_count': count, 'marker_color': (4, 5, 6, 7, 9)[i % 5],
                    'marker_corner': ('top_left', 'top_right', 'bottom_left', 'bottom_right')[i % 4]}
        grid = g.generate(17, i, difficulty='hard', **controls)
        assert g.self_check(grid) == []
        assert independent_observations(grid) == controls
        assert g.observe_overrides(grid) == controls
        assert g.rule_mirror(grid) == oracle(grid)[0]


@pytest.mark.parametrize('relation', ['same', '', 1])
def test_invalid_size_relation_fails_visibly(relation):
    with pytest.raises((ValueError, TypeError)):
        g.generate(17, 0, size_relation=relation)


def test_none_size_relation_uses_default_schedule():
    for index in range(6):
        assert g.generate(17, index, size_relation=None) == g.generate(17, index)


def test_default_draws_retain_all_canonical_common_shape_classes():
    expected = {shape_key(oracle(p['input'])[1][0]) for p in canonical_pairs(g.TASK_ID, root=ROOT, labeled_only=True)}
    observed = {shape_key(oracle(g.generate(seed, index, difficulty='medium'))[1][0])
                for seed in (17, 41, 103) for index in range(480)}
    assert expected <= observed


@pytest.mark.parametrize('axis', ['grid_h', 'grid_w', 'common_count', 'motif_size',
                                 'marker_color', 'marker_corner', 'unique_quadrant'])
def test_none_existing_axis_matches_omission(axis):
    assert g.generate(17, 5, **{axis: None}) == g.generate(17, 5)


def load_probe():
    path = ROOT / 'generators' / g.TASK_ID / 'workspace/probe_curriculum.py'
    spec = importlib.util.spec_from_file_location('curriculum_probe_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_retains_exact_ambiguity_when_only_witness_becomes_query():
    probe = load_probe()
    # Literal labelled pairs model a rival that agrees on the first three pairs,
    # then misses the sole witness. No generator mirror supplies the expectation.
    pairs = [{'sample_index': i, 'input': [[3]], 'output': [[8]]} for i in range(4)]
    predictions = {'declared:example': [[[8]], [[8]], [[8]], [[3]]]}
    scores = [probe.analyze_window(pairs, predictions, qi) for qi in range(4)]
    assert [s['query_sample_index'] for s in scores if s['ambiguous']] == [3]
    ambiguity = scores[3]['ambiguities'][0]
    assert ambiguity['demo_sample_indices'] == [0, 1, 2]
    assert ambiguity['rival_query_output'] == [[3]]
    assert ambiguity['reference_query_output'] == [[8]]
    predictions['declared:example'][1] = [[3]]
    assert not any(probe.analyze_window(pairs, predictions, qi)['ambiguous'] for qi in range(4))


def test_probe_discovers_current_declarations_and_own_tree():
    probe = load_probe()
    assert find_root(probe.__file__) == ROOT
    assert set(probe.declarations(g)) == set(declarations())
    assert Path(probe.load_generator(ROOT).__file__).resolve() == (ROOT / 'generators' / g.TASK_ID / 'generator.py').resolve()
