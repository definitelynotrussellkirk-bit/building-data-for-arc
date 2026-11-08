"""Curriculum, boundary, and count-independence checks for native inputs."""
import importlib.util
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / 'workspace/parametric'


def load(name):
    spec = importlib.util.spec_from_file_location('endpoint_sampler_test_' + name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s = load('sampler')
f = load('native_family')


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_banks_have_six_demos_four_distinct_novel_queries(seed):
    banks = s.sample_banks(seed)
    assert set(banks) == {'train', 'test'}
    assert len(banks['train']) == 6 and len(banks['test']) == 4
    grids = banks['train'] + banks['test']
    assert len({frozen(grid) for grid in grids}) == 10
    for grid in grids:
        f.validate_grid(grid)


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_three_demos_teach_stage_original_blockers_and_invalid_colors(seed):
    train = s.generate_inputs(seed)['train']
    assert len(train) == 3
    assert any(f.apply(grid, {'clearance_stage': 'input'}) !=
               f.apply(grid, {'clearance_stage': 'painted'}) for grid in train)
    profiles = [f.validate_grid(grid) for grid in train]
    assert any(pair['blockers'] for profile in profiles for pair in profile['pairs'])
    counts = [len(cells) for profile in profiles for cells in profile['by_color'].values()]
    assert 1 in counts and 3 in counts
    assert any(len(cells) == 2 and not f.segment(*cells)
               for profile in profiles for cells in profile['by_color'].values())
    assert any(len(pair['path']) == 2 for profile in profiles for pair in profile['pairs'])
    assert {'horizontal', 'vertical'} == {
        pair['orientation'] for profile in profiles for pair in profile['pairs']}
    # The third lesson is a canonical-role anchor with no erased color.
    assert set(profiles[2]['by_color']) == {
        value for row in f.apply(train[2], {'clearance_stage': 'input'}) for value in row if value}


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_first_demo_contains_accepted_rejected_accepted_chain(seed):
    grid = s.generate_inputs(seed)['train'][0]
    pairs = f.validate_grid(grid)['pairs']
    status = {row['color']: row['accepted'] for row in f.trace(grid, {'clearance_stage':'painted'})['steps']}
    witnessed = False
    for a in pairs:
        for b in pairs:
            for c in pairs:
                if not a['color'] < b['color'] < c['color']:
                    continue
                pa, pb, pc = map(lambda p: set(p['path'][1:-1]), (a,b,c))
                if (pa & pb and pb & pc and not pa & pc
                        and not a['blockers'] and not b['blockers'] and not c['blockers']
                        and status[a['color']] and not status[b['color']] and status[c['color']]):
                    witnessed = True
    assert witnessed


def test_first_demo_retains_older_accepted_path_after_another_acceptance():
    for seed in (0, 17, 2**63 - 1):
        grid = s.generate_inputs(seed)['train'][0]
        pairs = f.validate_grid(grid)['pairs']
        status = {row['color']: row['accepted']
                  for row in f.trace(grid, {'clearance_stage':'painted'})['steps']}
        clear = [pair for pair in pairs if not pair['blockers']]
        witnessed = False
        for a in clear:
            for b in clear:
                for c in clear:
                    for d in clear:
                        if not a['color'] < b['color'] < c['color'] < d['color']:
                            continue
                        pa, pb, pc, pd = [set(pair['path'][1:-1]) for pair in (a,b,c,d)]
                        if (pa & pb and pb & pc and not pa & pc and pa & pd
                                and not pc & pd
                                and [status[pair['color']] for pair in (a,b,c,d)] == [True,False,True,False]):
                            witnessed = True
        assert witnessed, 'A later pair must still see an older accepted path after an intervening acceptance'


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_query_boundaries_have_actual_content(seed):
    queries = s.sample_banks(seed)['test']
    small = next(grid for grid in queries if len(grid) == len(grid[0]) == 3)
    large = next(grid for grid in queries if len(grid) == len(grid[0]) == 30)
    assert sum(value != 0 for row in small for value in row) == 4
    info = f.validate_grid(large)
    assert len(info['pairs']) == 9
    assert set(info['by_color']) == set(range(1,10))
    assert all(len(cells) == 2 for cells in info['by_color'].values())
    assert all(not pair['blockers'] for pair in info['pairs'])
    for mode in f.MODES:
        output = f.apply(large, {'clearance_stage': mode})
        cells = [(r,c) for r,row in enumerate(output) for c,value in enumerate(row) if value]
        assert len(cells) >= 140
        assert {0,29} <= {r for r,c in cells}
        assert {0,29} <= {c for r,c in cells}


@pytest.mark.parametrize('demos', [3,4,5,6])
@pytest.mark.parametrize('queries', [1,2,3,4])
def test_independent_counts_are_prefixes_of_complete_shuffled_banks(demos, queries):
    full = s.sample_banks(17)
    actual = s.generate_inputs(17, demos=demos, queries=queries)
    assert actual == {'train':full['train'][:demos], 'test':full['test'][:queries]}


@pytest.mark.parametrize('seed', [True, -1, 2**63, 0.0, '0', None])
def test_seed_is_strict(seed):
    with pytest.raises((TypeError,ValueError)):
        s.sample_banks(seed)


@pytest.mark.parametrize('kwargs', [{'demos':2},{'demos':7},{'demos':True},{'demos':3.0},
                                  {'queries':0},{'queries':5},{'queries':False},{'queries':'4'}])
def test_counts_are_strict(kwargs):
    with pytest.raises((TypeError,ValueError)):
        s.generate_inputs(0, **kwargs)


def test_determinism_fresh_results_and_global_random_isolation():
    state = random.getstate()
    one = s.sample_banks(17)
    assert random.getstate() == state
    two = s.sample_banks(17)
    assert one == two
    one['train'][0][0][0] = 99
    one['test'][0].clear()
    assert two == s.sample_banks(17)


def test_complete_query_bank_is_not_always_asked_in_source_order():
    orders = [tuple((len(g),len(g[0])) for g in s.sample_banks(seed)['test']) for seed in range(8)]
    assert len(set(orders)) > 1
    assert len({order[0] for order in orders}) > 1
