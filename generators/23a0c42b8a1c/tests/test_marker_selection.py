"""Portable regressions for canonical support, honest controls and teaching.

Racket remains the label authority. These fast tests inspect input geometry;
the semantic battery and source-bound census verify the actual Racket outputs.
"""
from __future__ import annotations

from collections import Counter
import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator
from puzzle_generators.helpers.selfcheck import components

ROOT = find_root(__file__)
GEN, SOURCE, SHA256 = load_selected_generator('23a0c42b8a1c', root=ROOT)
PAIRS = canonical_pairs('23a0c42b8a1c', root=ROOT)


def parts(grid):
    comps = components(grid)
    marker = next(c for c in comps if c['color'] == 1)
    mr, mc = marker['cells'][0]
    adjacent = [c for c in comps if c['color'] != 1 and
                any(abs(r - mr) + abs(col - mc) == 1 for r, col in c['cells'])]
    ordered = sorted(adjacent, key=lambda c: min(c['cells']))
    target = min(adjacent, key=lambda c: (len(c['cells']), min(c['cells'])))
    return marker, ordered, target


@pytest.mark.parametrize('pair', PAIRS, ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_canonical_inputs_are_in_domain(pair):
    assert GEN.self_check(pair['input']) == []


@pytest.mark.parametrize('size', range(1, 8))
@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_small_size_is_realized_exactly(size, band):
    grid = GEN.generate(101, 1, difficulty=band, small_size=size)
    assert GEN.self_check(grid) == []
    assert len(parts(grid)[2]['cells']) == size


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_global_grid_bounds_hold_in_every_difficulty(band):
    for h, w in [(7, 8), (20, 19)]:
        grid = GEN.generate(17, 1, difficulty=band, grid_h=h, grid_w=w, small_size=7)
        assert (len(grid), len(grid[0])) == (h, w)
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize('ncolors', [4, 5, 6])
def test_declared_colour_count_is_observable(ncolors):
    grid = GEN.generate(13, 2, n_distinct_colors=ncolors)
    assert len({v for row in grid for v in row}) == ncolors
    assert GEN.observe_overrides(grid)['n_distinct_colors'] == ncolors


@pytest.mark.parametrize('axis,value', [('grid_h', True), ('grid_w', 11.0),
                                      ('small_size', '3'), ('n_distinct_colors', False)])
def test_exact_integer_controls_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7, 0, **{axis: value})


def test_unknown_controls_are_rejected():
    with pytest.raises(ValueError, match='[Uu]nknown|[Uu]nsupported'):
        GEN.generate(7, 0, typo_small_size=1)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_distribution_has_canonical_profile_support(band):
    wanted = {(len(p['input']), len(p['input'][0]),
               len({v for row in p['input'] for v in row})) for p in PAIRS}
    profiles = []
    for i in range(20):
        grid = GEN.generate(0, i, difficulty=band)
        profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert sum(p in wanted for p in profiles) >= 1, (band, Counter(profiles))


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_every_cyclic_five_pair_window_has_repeated_order_witnesses(band):
    for seed in [0, 17, 101]:
        for start in range(5):
            categories = Counter()
            for i in range(start, start + 5):
                _, adjacent, target = parts(GEN.generate(seed, i, difficulty=band))
                if len(adjacent) == 1:
                    categories['single'] += 1
                elif target is adjacent[0]:
                    categories['first'] += 1
                else:
                    categories['last'] += 1
            assert categories == {'first': 2, 'last': 2, 'single': 1}, (seed, start, categories)


def test_target_approaches_marker_from_all_four_directions():
    directions = set()
    for i in range(180):
        marker, _, target = parts(GEN.generate(37, i, difficulty='medium'))
        mr, mc = marker['cells'][0]
        for r, c in target['cells']:
            if abs(r - mr) + abs(c - mc) == 1:
                directions.add((r - mr, c - mc))
    assert directions == {(-1, 0), (1, 0), (0, -1), (0, 1)}


@pytest.mark.parametrize('grid', [[], [[0, 1], [2]], [[False, 1], [2, 0]],
                                [[0, 1], [2, 12]], [[0, 0], [0, 0]]])
def test_malformed_or_markerless_grids_are_rejected_without_crashing(grid):
    assert GEN.self_check(grid)


def test_ties_among_larger_neighbors_are_outside_executable_domain():
    # The current canonical comparator calls grid top-left on object hashes
    # whenever ANY compared neighbor sizes tie. Even a unique minimum is unsafe.
    grid = [[0, 0, 4, 0, 0],
            [0, 0, 1, 6, 6],
            [0, 0, 7, 0, 0],
            [0, 0, 7, 0, 0]]
    assert GEN.self_check(grid)


@pytest.mark.parametrize('axis,value',
    [('seed', v) for v in [True, False, 1.0, 1.75, '1']] +
    [('sample_index', v) for v in [True, False, 1.0, 1.75, '1', -1]] +
    [('difficulty', v) for v in [True, False, 0, 1.0, '__invalid_difficulty__']])
@pytest.mark.parametrize('band', ['easy', None, 'hard'])
def test_call_arguments_reject_invalid_scalars(axis, value, band):
    args = {'seed': 991, 'sample_index': 0, 'difficulty': band}
    args[axis] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**args)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_ordinary_inputs_include_unambiguous_singleton_marker_role(band):
    # Every canonical input has one singleton object, the color-1 marker.
    # Keep this useful visual role in ordinary support while also teaching
    # target-only masking with foreign singleton cells in other examples.
    singleton_counts = [sum(len(c['cells']) == 1 for c in components(
        GEN.generate(991, i, difficulty=band))) for i in range(10)]
    assert 1 in singleton_counts, singleton_counts
