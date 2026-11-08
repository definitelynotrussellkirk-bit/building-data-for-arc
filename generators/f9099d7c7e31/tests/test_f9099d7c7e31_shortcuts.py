"""Distribution regressions. Selectors are independent of generator internals."""
from __future__ import annotations

import pytest

from puzzle_generators.per_puzzle.f9099d7c7e31 import generator as gen


def objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if (0 <= yy < h and 0 <= xx < w and
                            (yy, xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            r0, r1 = min(y for y, _ in cells), max(y for y, _ in cells)
            c0, c1 = min(x for _, x in cells), max(x for _, x in cells)
            result.append(dict(h=r1-r0+1, w=c1-c0+1, n=len(cells),
                               bbox=(r0, c0, r1, c1)))
    return result


def crop(grid, obj):
    r0, c0, r1, c1 = obj['bbox']
    return [row[c0:c1+1] for row in grid[r0:r1+1]]


def selected(grid):
    return max(objects(grid), key=lambda o: (o['w'], o['n']))


def largest_bbox(grid):
    return crop(grid, max(objects(grid), key=lambda o: (o['w']*o['h'], o['w'], o['n'])))


def widest_tallest(grid):
    return crop(grid, max(objects(grid), key=lambda o: (o['w'], o['h'], o['n'])))


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('start', range(4))
@pytest.mark.parametrize('rival', [largest_bbox, widest_tallest])
def test_every_four_slot_window_refutes_correlated_geometry(band, start, rival):
    grids = [gen.generate(431, i, difficulty=band) for i in range(start, start+4)]
    assert any(rival(g) != crop(g, selected(g)) for g in grids), rival.__name__


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_complete_lesson_includes_strictly_interior_target(band):
    grids = [gen.generate(17, i, difficulty=band) for i in range(4)]
    assert any(0 < selected(g)['bbox'][0] and 0 < selected(g)['bbox'][1]
               and selected(g)['bbox'][2] < len(g)-1
               and selected(g)['bbox'][3] < len(g[0])-1 for g in grids)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_two_canonical_shape_anchors_are_retained(band):
    for seed in [0, 17, 431, 9917]:
        for i in (0, 3):
            g = gen.generate(seed, i, difficulty=band)
            assert gen.strict_canonical_like(g) == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_old_axis_contract_and_purity_survive(band):
    opts = dict(grid_h=9, grid_w=11, n_objects=3, target_width=4,
                target_height=2, selection_mode='width_tie_size',
                intruder_in_crop=True, larger_narrow_decoy=True)
    saved = opts.copy()
    a = gen.generate(9917, 2, difficulty=band, **opts)
    assert gen.self_check(a) == []
    assert gen.observe_overrides(a) == opts
    assert opts == saved
    assert gen.generate(9917, 2, difficulty=band, **opts) == a


def test_new_counterexamples_are_visible_to_standard_semantic_gate():
    required = {'largest_bbox_area', 'widest_then_tallest', 'border_only'}
    assert required <= gen.SEMANTIC_RIVALS.keys()
    assert required <= {r for values in gen.WITNESS_RIVALS.values() for r in values}
    grids = [gen.generate(431, i, difficulty='medium') for i in range(4)]
    for name in required:
        assert any(gen.SEMANTIC_RIVALS[name](g) != crop(g, selected(g)) for g in grids)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_geometry_fix_does_not_invert_the_height_shortcut(band):
    grids = [gen.generate(431, i, difficulty=band) for i in range(4)]
    def shortest(g):
        return crop(g, max(objects(g), key=lambda o: (o['w'], -o['h'], o['n'])))
    assert any(shortest(g) != crop(g, selected(g)) for g in grids)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_fresh_solve_prefix_teaches_border_independence(band):
    pairs = []
    for i in range(5):
        g = gen.generate(431, i, difficulty=band)
        pairs.append({'input': g, 'output': crop(g, selected(g))})
    for q in pairs[3:]:
        assert gen.lesson_identifiable(pairs[:3], q) == []
