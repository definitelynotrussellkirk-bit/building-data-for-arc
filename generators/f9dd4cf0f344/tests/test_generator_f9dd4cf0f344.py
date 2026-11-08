"""Task-local tests; run explicitly because repository testpaths is tests/."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME/'workspace'))
from quality_probe import load_generator, oracle, rival

gen = load_generator()


def test_explicit_dimensions_and_fill_count_are_honored():
    g = gen.generate(0, 0, grid_h=11, grid_w=15, pluses=3, n_decoys=0)
    assert (len(g),len(g[0])) == (11,15)
    assert sum(a != b for x,y in zip(g,oracle(g)) for a,b in zip(x,y)) == 3


@pytest.mark.parametrize('kw', [{'typo':4}, {'grid_h':True}, {'grid_w':7.9},
                                {'pluses':-1}, {'grid_h':4}, {'n_decoys':9},
                                {'texture':'not_a_texture'}])
def test_invalid_or_unknown_overrides_fail_loudly(kw):
    with pytest.raises(ValueError):
        gen.generate(0,0,**kw)


def test_impossible_packing_never_silently_falls_back():
    with pytest.raises(ValueError):
        gen.generate(0,0,grid_h=5,grid_w=5,pluses=8,n_decoys=8)


@pytest.mark.parametrize('texture,name', [('near_miss','enclosed_majority'),
                                        ('occupied','overwrite_occupied'),
                                        ('diagonal','diagonals_also')])
def test_targeted_textures_falsify_wrong_rules(texture,name):
    for seed in range(12):
        g = gen.generate(seed,0,grid_h=11,grid_w=15,pluses=2,n_decoys=2,texture=texture)
        assert rival(g,name) != oracle(g)
        assert gen.observe_overrides(g)['n_decoys'] == 2
        assert gen.observe_overrides(g)['pluses'] == 2


@pytest.mark.parametrize('texture', ['no_pluses','partial_arms','mismatched_arms'])
def test_explicit_lawful_negative_controls(texture):
    g = gen.generate(12,3,grid_h=9,grid_w=13,texture=texture)
    assert (len(g),len(g[0])) == (9,13)
    assert g == oracle(g)
    assert not gen.self_check(g,meta={'texture':texture})


@pytest.mark.parametrize('difficulty',[None,'easy','medium','hard'])
def test_default_repeatability_purity_and_nonidentity(difficulty):
    for seed in range(30):
        g = gen.generate(seed,seed,difficulty=difficulty)
        assert g == gen.generate(seed,seed,difficulty=difficulty)
        old = deepcopy(g)
        assert not gen.self_check(g)
        assert g == old
        assert oracle(g) != g


@pytest.mark.parametrize('grid',[[], [[]], [[0],[0,1]], [[False]*7 for _ in range(7)],
                                 [[10]*7 for _ in range(7)], [[0]*7 for _ in range(7)]])
def test_self_check_rejects_malformed_or_default_uninformative_grids(grid):
    assert gen.self_check(grid)


def test_generated_outputs_are_idempotent_and_preserve_input_nonzero_cells():
    for seed in range(30):
        g = gen.generate(seed,0)
        out = oracle(g)
        assert oracle(out) == out
        assert all(a == b for x,y in zip(g,out) for a,b in zip(x,y) if a != 0)


def test_known_rival_is_not_a_duplicate_oracle():
    g = [[0]*5 for _ in range(5)]
    g[1][2]=g[3][2]=g[2][1]=4
    g[2][3]=7
    assert oracle(g) == g
    assert rival(g,'enclosed_majority')[2][2] == 4


@pytest.mark.parametrize('axis', ['pluses','n_decoys'])
@pytest.mark.parametrize('difficulty', ['easy','medium','hard'])
def test_single_count_override_resizes_unpinned_canvas(axis,difficulty):
    for count in range(9):
        for seed in range(5):
            kw = {axis:count}
            g = gen.generate(seed,0,difficulty=difficulty,**kw)
            assert gen.observe_overrides(g)[axis] == count
            assert not gen.self_check(g,meta=kw)


def test_joint_high_counts_fit_when_canvas_is_not_pinned():
    g = gen.generate(1,0,pluses=8,n_decoys=8)
    assert gen.observe_overrides(g)['pluses'] == 8
    assert gen.observe_overrides(g)['n_decoys'] == 8


def test_explicit_mode_conflict_identifies_only_incompatible_axes():
    with pytest.raises(ValueError) as err:
        gen.generate(1,0,texture='plain',n_decoys=1)
    assert set(err.value.incompatible_axes) == {'texture','n_decoys'}
