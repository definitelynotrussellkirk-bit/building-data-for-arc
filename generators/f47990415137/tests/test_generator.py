"""Selected-task tests run in both the library and the copied task-test runtime."""
import json
import sys
from pathlib import Path
from copy import deepcopy
import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / 'workspace'))
from probe import load_generator, canonical, objects, dimensions, aspect, python_oracle, observation

gen = load_generator()


def test_rule_pin():
    assert getattr(gen, 'RULE_HASH', None) == '5cf35af61edf'


@pytest.mark.parametrize('pair', canonical(), ids=['train0','train1','train2','test0'])
def test_canonical_acceptance_and_independent_oracle(pair):
    assert gen.self_check(pair['input']) == []
    assert python_oracle(pair['input']) == pair['output']


@pytest.mark.parametrize('band', [None,'easy','medium','hard'])
@pytest.mark.parametrize('n,k', [(3,1),(3,3),(4,3),(5,2),(6,6)])
def test_joint_exact_controls(band, n, k):
    requested = dict(grid_h=8, grid_w=8, n_blobs=n, n_distinct_colors=k)
    g = gen.generate(29, 17, difficulty=band, **requested)
    assert observation(g) == requested
    assert gen.observe_overrides(g) == requested
    assert gen.self_check(g) == []


@pytest.mark.parametrize('key,value', [('typo',1),('grid_h',7),('grid_w',21),
    ('grid_h',True),('grid_w',10.5),('n_blobs',2),('n_blobs',7),
    ('n_distinct_colors',0),('n_distinct_colors',7),('n_blobs','4'),
    ('palette_kind','warm'),('palette_size',3),('density','sparse'),
    ('position_bias','spread_oriented'),('texture','all_squares')])
def test_invalid_or_removed_controls_reject(key, value):
    with pytest.raises(ValueError): gen.generate(0, 0, **{key:value})


def test_incompatible_palette_count_rejects_with_axis_evidence():
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, n_blobs=3, n_distinct_colors=4)
    assert set(exc.value.incompatible_axes) == {'n_blobs','n_distinct_colors'}


@pytest.mark.parametrize('k', range(1,7))
def test_each_palette_override_can_be_requested_alone(k):
    g = gen.generate(7, 9, n_distinct_colors=k)
    assert observation(g)['n_distinct_colors'] == k
    assert gen.self_check(g) == []


@pytest.mark.parametrize('grid', [[],[[]],[[0]],[[0],[1,2]],[[True,0]],[[10,0]],[[1.5]],['00'],[[],[]]])
def test_invalid_grids_are_reported_not_crashes(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize('band', ['easy','medium','hard'])
def test_defaults_refute_both_canonical_shortcuts_per_input(band):
    signatures = set(); shape_sizes = []; placements = set()
    for i in range(128):
        g = gen.generate(91000+i, i*7+2, difficulty=band)
        assert gen.self_check(g) == []
        assert gen.strict_canonical_like(g) == []
        assert {aspect(cells) for _,cells in objects(g)} == {2,3,4}
        assert python_oracle(g) != python_oracle(g, by_color=True)
        assert python_oracle(g) != python_oracle(g, fill=True)
        assert g == gen.generate(91000+i, i*7+2, difficulty=band)
        before = deepcopy(g)
        for rival in gen.LESSON_COMPETITORS.values(): rival(g)
        assert g == before
        signatures.add(json.dumps(g)); placements.add(aspect(objects(g)[0][1]))
        shape_sizes.extend(len(cells) for _,cells in objects(g))
    assert len(signatures) == 128
    assert max(shape_sizes) >= 15
    assert placements == {2,3,4}


def test_every_declared_canonical_shortcut_actually_fits_all_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == {'group_by_color','fill_bounding_boxes'}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in canonical()), name


def test_forced_constructive_fallback_keeps_counts_and_witnesses(monkeypatch):
    monkeypatch.setattr(gen, '_place_shape', lambda *args, **kwargs: None)
    for n in range(3,7):
        g = gen.generate(21,n,grid_h=8,grid_w=8,n_blobs=n,n_distinct_colors=min(3,n-1))
        assert observation(g)['n_blobs'] == n
        assert gen.self_check(g) == []
        assert python_oracle(g) != python_oracle(g,by_color=True)
        assert python_oracle(g) != python_oracle(g,fill=True)
