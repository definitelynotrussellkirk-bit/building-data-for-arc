"""Native orbit curriculum: count stability, geometry and source-side teaching."""
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'
SPEC = importlib.util.spec_from_file_location('orbit_native_sampler_tested', HOME / 'sampler.py')
sampler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sampler)

SEEDS = (0, 17, 2**63 - 1)


def info(grid):
    """Inspect the public input contract independently of the constructor."""
    assert type(grid) is list and 6 <= len(grid) <= 30
    height, width = len(grid), len(grid[0])
    assert 6 <= width <= 30
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)}
    colors = {grid[r][c] for r, c in cells}
    assert len(anchors) == len(colors) == 1
    assert 3 <= len(cells) <= 14**2
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    assert seen == cells
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    shape = (r1 - r0 + 1, c1 - c0 + 1)
    assert all(2 <= size <= 14 for size in shape)
    ar, ac = anchors[0]
    m = max(shape)
    assert m + 1 <= ar <= height - m - 1
    assert m + 1 <= ac <= width - m - 1
    sides = []
    if r1 <= ar - 2 and c0 <= ac <= c1:
        sides.append('above')
    if c0 >= ac + 2 and r0 <= ar <= r1:
        sides.append('right')
    if r0 >= ar + 2 and c0 <= ac <= c1:
        sides.append('below')
    if c1 <= ac - 2 and r0 <= ar <= r1:
        sides.append('left')
    assert len(sides) == 1
    return {'canvas': (height, width), 'shape': shape, 'anchor': anchors[0],
            'side': sides[0], 'color': next(iter(colors)), 'area': len(cells),
            'local': frozenset((r - r0, c - c0) for r, c in cells),
            'bbox': (r0, c0, r1, c1)}


def signature(grid):
    return json.dumps(grid, separators=(',', ':'))


@pytest.mark.parametrize('seed', SEEDS)
def test_minimum_curriculum_teaches_all_four_source_sides(seed):
    episode = sampler.generate_inputs(seed)
    assert len(episode['train']) == len(episode['test']) == 4
    facts = [info(grid) for grid in episode['train']]
    assert {fact['side'] for fact in facts} == {'above', 'right', 'below', 'left'}
    assert all(fact['anchor'] != tuple(size // 2 for size in fact['canvas']) for fact in facts)


@pytest.mark.parametrize('seed', SEEDS)
def test_matched_pairs_isolate_side_without_palette_or_geometry_changes(seed):
    facts = [info(grid) for grid in sampler.generate_inputs(seed)['train']]
    for first, second in ((facts[0], facts[1]), (facts[2], facts[3])):
        for field in ('canvas', 'anchor', 'local', 'color'):
            assert first[field] == second[field]
        assert first['side'] != second['side']
        assert first['shape'][0] != first['shape'][1]
    assert {facts[0]['side'], facts[1]['side']} == {'above', 'right'}
    assert {facts[2]['side'], facts[3]['side']} == {'below', 'left'}
    assert facts[0]['color'] != facts[2]['color']
    assert facts[0]['area'] != facts[2]['area']
    assert facts[0]['area'] > 4 and facts[2]['area'] > 4


@pytest.mark.parametrize('seed', SEEDS)
def test_all_count_requests_preserve_complete_bank_prefixes(seed):
    full = sampler.sample_banks(seed)
    assert len(full['train']) == 6 and len(full['test']) == 4
    for demos in range(4, 7):
        for queries in range(1, 5):
            requested = sampler.generate_inputs(seed, demos=demos, queries=queries)
            assert requested == {'train': full['train'][:demos], 'test': full['test'][:queries]}
    all_grids = full['train'] + full['test']
    assert len({signature(grid) for grid in all_grids}) == 10
    for grid in all_grids:
        info(grid)


@pytest.mark.parametrize('seed', SEEDS)
def test_query_bank_contains_real_minimum_and_substantive_large_content(seed):
    queries = sampler.generate_inputs(seed)['test']
    facts = [info(grid) for grid in queries]
    assert sorted(fact['canvas'] for fact in facts) == [(6, 6), (18, 20), (25, 27), (30, 30)]
    smallest = next(fact for fact in facts if fact['canvas'] == (6, 6))
    largest = next(fact for fact in facts if fact['canvas'] == (30, 30))
    assert smallest['area'] == 3 and smallest['shape'] == (2, 2)
    assert largest['shape'] == (14, 14) and largest['area'] >= 120
    assert largest['anchor'] == (15, 15)
    assert smallest['side'] in ('above', 'left')
    assert largest['side'] in ('above', 'left')
    assert next(fact for fact in facts if fact['canvas'] == (18, 20))['area'] >= 30
    assert next(fact for fact in facts if fact['canvas'] == (25, 27))['area'] >= 55


class IntSubclass(int):
    pass


@pytest.mark.parametrize('seed', [True, False, -1, 2**63, 1.0, '17', None, IntSubclass(0)])
def test_invalid_seeds_fail_explicitly(seed):
    with pytest.raises((TypeError, ValueError)):
        sampler.generate_inputs(seed)
    with pytest.raises((TypeError, ValueError)):
        sampler.sample_banks(seed)


@pytest.mark.parametrize('argument,value', [
    ('demos', 3), ('demos', 7), ('demos', True), ('demos', 4.0), ('demos', '4'),
    ('demos', None), ('demos', IntSubclass(4)),
    ('queries', 0), ('queries', 5), ('queries', False), ('queries', 1.0),
    ('queries', '1'), ('queries', None), ('queries', IntSubclass(1)),
])
def test_invalid_counts_fail_explicitly(argument, value):
    with pytest.raises((TypeError, ValueError)):
        sampler.generate_inputs(0, **{argument: value})


def test_fresh_mutable_results_do_not_touch_global_random_state():
    state = random.getstate()
    first = sampler.generate_inputs(17, demos=6)
    expected = sampler.generate_inputs(17, demos=6)
    assert first == expected
    rows = [row for grid in first['train'] + first['test'] for row in grid]
    assert len({id(row) for row in rows}) == len(rows)
    first['train'][0][0][0] = 9
    first['test'][0][0][0] = 9
    first['train'].pop()
    assert sampler.generate_inputs(17, demos=6) == expected
    assert random.getstate() == state


def test_full_query_shuffle_changes_size_order_across_seeds_and_keeps_prefixes():
    orders = []
    for seed in range(8):
        full = sampler.generate_inputs(seed)
        order = tuple((len(grid), len(grid[0])) for grid in full['test'])
        orders.append(order)
        assert sampler.generate_inputs(seed, queries=1)['test'] == full['test'][:1]
        assert sampler.generate_inputs(seed)['test'] == full['test']
    assert len(set(orders)) >= 3
    assert len({order[0] for order in orders}) >= 2


def test_distinct_seeds_change_palette_placement_and_geometry():
    banks = [sampler.generate_inputs(seed) for seed in SEEDS]
    assert len({signature(bank['train'][0]) for bank in banks}) == len(SEEDS)
    assert len({tuple(info(grid)['color'] for grid in bank['train']) for bank in banks}) >= 2
    assert len({info(bank['train'][0])['local'] for bank in banks}) >= 2
