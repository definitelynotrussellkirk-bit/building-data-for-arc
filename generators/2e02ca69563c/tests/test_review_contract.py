"""Regression tests for review-361d29beeb4e7c05, with no private runner calls."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load('routing_review_generator',HOME/'generator.py')
ref = load('routing_review_oracle',HOME/'workspace/review_oracle.py')


def test_rule_is_pinned():
    assert getattr(gen,'RULE_HASH',None) == '024c6f6dd0fa'


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_exact_controls_from_pixels(band):
    request = dict(grid_h=21,grid_w=23,n_frames=3,frame_h=6,frame_w=7,
                   pairs_per_frame=2,frame_color=5,shared_pairs=1,n_ignored=3)
    grid = gen.generate(17,4,difficulty=band,**request)
    obs = gen.observe_overrides(grid)
    assert {name:obs[name] for name in request} == request
    assert gen.self_check(grid) == []
    assert not ref.path_conflicts(grid)


@pytest.mark.parametrize('name,value',[('typo',2),('texture','warm'),('palette_size',4)])
def test_unknown_and_retired_controls_are_rejected(name,value):
    with pytest.raises((ValueError,TypeError,KeyError)):
        gen.generate(0,0,**{name:value})


@pytest.mark.parametrize('value',[True,1.5,'2'])
def test_integer_controls_do_not_coerce_invalid_types(value):
    with pytest.raises(ValueError):
        gen.generate(0,0,n_frames=value)


@pytest.mark.parametrize('grid',[
    [], [[]], [[0,0],[0]], [[0]*8 for _ in range(8)], [[0,10],[0,0]],
    [[0,False],[0,0]], [[0,2,0],[0,0,0],[0,0,0]],
])
def test_validator_rejects_malformed_or_frameless_inputs(grid):
    assert gen.self_check(grid)


def test_broken_frame_is_rejected():
    g = ref.hand_witness()
    g[1][2] = 0
    assert gen.self_check(g)


def test_reference_domain_allows_reused_colors():
    grid = ref.hand_witness()
    assert gen.self_check(grid) == []
    assert ref.solve_reference(grid) != grid


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_lawful_noncolliding_draws_and_determinism(band):
    for seed in range(12):
        for index in range(3):
            g = gen.generate(seed,index,difficulty=band)
            assert g == gen.generate(seed,index,difficulty=band)
            assert gen.self_check(g) == [], (seed,index,gen.self_check(g))
            assert not ref.path_conflicts(g), (seed,index,ref.path_conflicts(g))
            for frame in ref.frames(g):
                assert any(len(p)==2 for p in ref.groups(g,frame).values())


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_every_cyclic_three_demo_lesson_refutes_declared_rivals(band):
    rivals = getattr(gen,'LESSON_COMPETITORS',{})
    assert rivals, 'Executable lesson competitors are required'
    for seed in range(5):
        samples = [gen.generate(seed,j,difficulty=band) for j in range(5)]
        for start in range(3):
            demos = samples[start:start+3]
            for name,rival in rivals.items():
                assert any(rival(copy.deepcopy(g)) != ref.solve_reference(g) for g in demos), (seed,start,name)


def test_impossible_combination_reports_axes_instead_of_dropping_frames():
    with pytest.raises(ValueError) as caught:
        gen.generate(0,0,grid_h=9,grid_w=9,n_frames=3,frame_h=10,frame_w=10)
    assert set(caught.value.incompatible_axes) >= {'grid_h','grid_w','n_frames','frame_h','frame_w'}


def test_single_frame_cannot_claim_cross_frame_reuse():
    with pytest.raises(ValueError) as caught:
        gen.generate(0,0,n_frames=1,shared_pairs=1)
    assert {'n_frames','shared_pairs'} <= set(caught.value.incompatible_axes)


def test_self_check_does_not_mutate_input():
    grid = ref.hand_witness()
    before = copy.deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == before
