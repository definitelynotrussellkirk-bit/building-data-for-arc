"""Window membership examples; protected-reference execution is a separate gate."""
import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1] / 'workspace/parametric'


def load():
    spec = importlib.util.spec_from_file_location('_solid_window_parameters', HOME / 'adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_the_exact_canonical_resource():
    module = load()
    assert module.program({'window_size': 2, 'minimum_overlap': 1}) == (HOME / 'canonical.rkt').read_text()


@pytest.mark.parametrize('window,minimum', [(2, 1), (2, 2), (3, 1), (3, 2)])
def test_membership_counts_are_from_the_original_scene(window, minimum):
    module = load()
    grid = [[5]*4 for _ in range(4)]
    expected = []
    for r in range(4):
        row = []
        for c in range(4):
            count = sum(r0 <= r < r0+window and c0 <= c < c0+window
                        for r0 in range(5-window) for c0 in range(5-window))
            row.append(1 if count >= minimum else 5)
        expected.append(row)
    before = [row[:] for row in grid]
    setting = {'window_size': window, 'minimum_overlap': minimum}
    assert module.transform(grid, setting) == expected
    assert grid == before
    assert module.scan_rival(grid, setting) != expected


def test_counts_settings_and_query_prefixes_are_independent_and_distinct():
    module = load()
    for seed in (0, 17, 917):
        original = module.generate(seed, module.SETTINGS[0], 2, 4)
        for setting in module.SETTINGS:
            for demos in range(2, 7):
                episode = module.generate(seed, setting, demos, 4)
                assert [p['input'] for p in episode['test']] == [p['input'] for p in original['test']]
                assert [p['input'] for p in episode['train'][:2]] == [p['input'] for p in original['train']]
                assert len(episode['train']) == demos
                assert module.teaching_check(episode, setting)['survivors'] == [setting]
                assert module.teaching_check(episode, setting)['surviving_rivals'] == []
                inputs = [str(p['input']) for p in episode['train']+episode['test']]
                assert len(inputs) == len(set(inputs))
                large, = [p['input'] for p in episode['test'] if len(p['input']) == len(p['input'][0]) == 30]
                assert sum(v == 5 for row in large for v in row) >= 100
                assert all(p['input'] != p['output'] for p in episode['train']+episode['test'])
                for count in range(1, 5):
                    prefix = module.generate(seed, setting, demos, count)
                    assert prefix['test'] == episode['test'][:count]


def test_query_size_does_not_encode_a_fixed_query_position():
    module = load(); orders = set(); large_positions = set()
    for seed in range(8):
        episode = module.generate(seed,module.SETTINGS[0],2,4)
        order = tuple((len(p['input']),len(p['input'][0])) for p in episode['test'])
        orders.add(order); large_positions.add(order.index((30,30)))
    assert len(orders) > 1 and len(large_positions) > 1


def test_large_negative_components_and_gray_tails_teach_the_original_gap():
    module = load()
    episode = module.generate(17, module.SETTINGS[0], 2, 4)
    pair = episode['train'][0]
    assert module.rival_output(pair['input'], module.SETTINGS[0], 'component_area_ge4') != pair['output']
    assert module.rival_output(pair['input'], module.SETTINGS[0], 'whole_eligible_component') != pair['output']
    assert any(len(component) >= 4 and all(pair['output'][r][c] == 5 for r,c in component)
               for component in module.components(pair['input']))


@pytest.mark.parametrize('window,minimum', [(2,1),(2,2),(3,1),(3,2)])
def test_mandatory_unequal_overlapping_cores_reject_both_maximum_rectangle_shortcuts(window, minimum):
    module = load(); settings = {'window_size':window,'minimum_overlap':minimum}
    grid = [[5,5,5,5,0],[5,5,5,5,0],[5,5,5,5,5],[5,5,5,5,5],[0,5,5,5,5]]
    expected = module.transform(grid,settings)
    assert expected[4][2] == expected[4][3] == 1
    for rival in ('maximum_rectangle_rule','maximum_rectangle_mask'):
        assert module.rival_output(grid,settings,rival) != expected
        for seed in (0,1,17):
            episode = module.generate(seed,settings,2,4)
            assert any(module.rival_output(p['input'],settings,rival) != p['output'] for p in episode['train'])


@pytest.mark.parametrize('seed,setting,demos,queries', [
    (True, {'window_size': 2, 'minimum_overlap': 1}, 2, 4),
    (-1, {'window_size': 2, 'minimum_overlap': 1}, 2, 4),
    (0, {'window_size': True, 'minimum_overlap': 1}, 2, 4),
    (0, {'window_size': 2, 'minimum_overlap': 1.0}, 2, 4),
    (0, {'window_size': 2, 'minimum_overlap': 1, 'unknown': 2}, 2, 4),
    (0, {'window_size': 2, 'minimum_overlap': 1}, 1, 4),
    (0, {'window_size': 2, 'minimum_overlap': 1}, 7, 4),
    (0, {'window_size': 2, 'minimum_overlap': 1}, 2, True),
    (0, {'window_size': 2, 'minimum_overlap': 1}, 2, 5),
])
def test_invalid_requests_fail_explicitly(seed, setting, demos, queries):
    with pytest.raises(ValueError):
        load().generate(seed, setting, demos, queries)


@pytest.mark.parametrize('grid', [[], [[]], [[True]], [[5.0]], [[-1]], [[10]], [[5],[0,5]]])
def test_transform_rejects_malformed_or_coerced_grids(grid):
    module = load()
    with pytest.raises(ValueError): module.transform(grid,module.SETTINGS[0])
