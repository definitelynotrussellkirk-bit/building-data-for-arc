"""Regressions written against the unchanged baseline before repair."""
from copy import deepcopy
import os
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME/'workspace'))
from probe import components, load_generator, local_neighbor_output, observed, pairs

gen = load_generator(os.environ.get('GENERATOR_UNDER_TEST'))


def test_rule_is_pinned():
    assert getattr(gen, 'RULE_HASH', None) == '8f9e53b42241'


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_easy_keeps_multi_object_teaching(band):
    for start in range(12):
        lesson = [gen.generate(180, start+i, difficulty=band) for i in range(3)]
        assert any(len(components(g)) >= 2 for g in lesson)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_exact_count_color_and_size_controls(band):
    controls = dict(grid_h=12, grid_w=12, rectangles=4, n_distinct_colors=2)
    grid = gen.generate(170, 1, difficulty=band, **controls)
    assert observed(grid) == controls
    assert gen.observe_overrides(grid) == controls
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_three_demo_windows_teach_repeated_colors(band):
    for start in range(24):
        grids = [gen.generate(192, start+i, difficulty=band) for i in range(3)]
        assert any(observed(g)['n_distinct_colors'] < observed(g)['rectangles'] for g in grids)
        assert any(any(p['bbox'][2]-p['bbox'][0]+1 >= 5 for p in components(g)) for g in grids)


@pytest.mark.parametrize('bad', [None, [], [[]], [[0],[0,1]], [[True]*9 for _ in range(9)], [[10]*9 for _ in range(9)]])
def test_bad_grids_produce_reasons_not_exceptions(bad):
    try:
        reasons = gen.self_check(bad)
    except Exception as exc:
        pytest.fail(f'validator crashed instead of returning reasons: {exc}')
    assert reasons


@pytest.mark.parametrize('key,value', [('unknown', 1),('grid_h',True),('grid_w',12.5),('rectangles','3'),('n_distinct_colors',0)])
def test_invalid_controls_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0,0,**{key:value})


@pytest.mark.parametrize('pair', pairs())
def test_canonical_domain_and_independent_oracle(pair):
    assert gen.self_check(pair['input']) == []
    assert local_neighbor_output(pair['input']) == pair['output']


def test_all_semantic_declarations_are_executable_and_true():
    assert getattr(gen,'CANONICAL_SHORTCUTS',{})
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in pairs()), name
    for index in range(18):
        grid = gen.generate(761, index)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                assert any(gen.SEMANTIC_RIVALS[r](grid) != local_neighbor_output(grid)
                           for r in gen.WITNESS_RIVALS[name]), name


def test_pixel_independence_and_determinism():
    a=gen.generate(982,2); saved=deepcopy(a)
    _=local_neighbor_output(a)
    assert a == saved == gen.generate(982,2)
    a[0][0]=9
    assert gen.generate(982,2) == saved


def test_difficulty_changes_defaults_not_control_domains():
    grids={band:[gen.generate(762,i,difficulty=band) for i in range(12)] for band in ('easy','medium','hard')}
    assert grids['easy'] != grids['medium']
    assert grids['medium'] != grids['hard']


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_boundary_controls_and_incompatible_color_counts(band):
    for h in (9,18):
        for w in (9,18):
            for count in range(1,5):
                for colors in range(1,count+1):
                    controls=dict(grid_h=h,grid_w=w,rectangles=count,n_distinct_colors=colors)
                    g=gen.generate(143,count+colors,difficulty=band,**controls)
                    assert gen.self_check(g)==[]
                    assert observed(g)==controls
    with pytest.raises(ValueError,match='n_distinct_colors.*rectangles'):
        gen.generate(3,0,difficulty=band,rectangles=1,n_distinct_colors=3)


def test_color_boundary_and_repeated_components_are_in_domain():
    g=[[0]*12 for _ in range(12)]
    for color,r0,c0 in [(2,1,1),(3,4,1),(2,7,6)]:
        for r in range(r0,r0+3):
            for c in range(c0,c0+4):g[r][c]=color
    assert gen.self_check(g)==[]
    assert observed(g)['rectangles']==3
    assert observed(g)['n_distinct_colors']==2
    # Shared edges of different colors survive, unlike color-blind erosion.
    assert local_neighbor_output(g)[3][2]==2
    assert local_neighbor_output(g)[4][2]==3
