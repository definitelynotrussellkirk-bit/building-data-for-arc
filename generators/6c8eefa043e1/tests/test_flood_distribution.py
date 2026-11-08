"""Regressions for seed ownership and an honest, canonical-supported sampler."""
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root

TASK='6c8eefa043e1'
HOME=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('flood_review_probe',HOME/'workspace/review_probe.py')
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
gen,SOURCE=probe.load_generator()


def test_rejects_two_seeds_in_one_actual_region():
    grid=[[0]*9 for _ in range(9)]
    for r,c in ((2,2),(2,6),(6,2),(6,6)): grid[r][c]=5
    grid[0][0]=1; grid[0][8]=3
    assert probe.domain_counts(grid)['collision_components']==1
    assert gen.self_check(grid), 'two seeds in one 4-connected region must be rejected'


def test_unknown_override_is_not_silently_swallowed():
    with pytest.raises(ValueError, match='unknown'):
        gen.generate(1,0,grdi_h=9)


def test_small_boundary_supports_all_five_seed_colors():
    grid=gen.generate(4,0,difficulty='hard',grid_h=7,grid_w=7,palette_size=5)
    assert len(grid)==7 and len(grid[0])==7
    assert len({v for row in grid for v in row}-{0,5})==5
    assert not gen.self_check(grid)
    assert probe.domain_counts(grid)['collision_components']==0


def test_canonical_inputs_remain_in_declared_domain():
    pairs=canonical_pairs(TASK,root=find_root(__file__),labeled_only=True)
    assert len(pairs)>=4
    for pair in pairs:
        assert not gen.self_check(pair['input'])
        assert probe.oracle(pair['input'])==pair['output']


def test_selected_authority_copies_match_canonical_exactly():
    import json
    from reviewer_support import canonical_path
    ledger=canonical_path(find_root(__file__))
    rules={row['program_solution'] for row in map(json.loads,ledger.read_text().splitlines()) if row.get('task_id')==TASK}
    assert len(rules)==1
    rule=rules.pop()
    for folder,filename in (('training','e69241bd__6c8eefa043e1.json'),('augmented','e69241bd__8cf7525dc41a.json')):
        data=json.loads((ledger.parent.parent/'base/solutions'/folder/filename).read_text())
        assert data['racket_target']['target_code']==rule


@pytest.mark.parametrize('bad',[None,[],[[]],[[0],[0,5]],['00'],[[True]],[[1.5]],[[10]],[['0']]])
def test_malformed_grid_returns_reasons(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('axis',['grid_h','grid_w','palette_size'])
@pytest.mark.parametrize('value',[True,7.0,'7',-1,100])
def test_noninteger_or_out_of_range_axis_rejected(axis,value):
    with pytest.raises(ValueError):
        gen.generate(1,0,**{axis:value})


@pytest.mark.parametrize('axis',['n_walls','wall_orientation','palette_kind','wall_position_bias','anchor_corner','asymmetry_force','texture'])
def test_retired_misleading_controls_fail_loudly(axis):
    with pytest.raises(ValueError,match='unknown'):
        gen.generate(1,0,**{axis:None})


def test_deterministic_pure_generation_and_none_override():
    import random
    state=random.getstate()
    a=gen.generate(9817,9,difficulty='hard')
    b=gen.generate(9817,9,difficulty='hard',grid_h=None)
    assert a==b
    assert random.getstate()==state
    b[0][0]=(b[0][0]+1)%10
    assert gen.generate(9817,9,difficulty='hard')==a


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_full_joint_axis_domain_and_rival_refutation(band):
    # 14 heights x 14 widths x 4 palettes = 784 combinations per band.
    # A production change that clips colors, changes bounds by band, merges
    # seeds, or stops teaching a declared rival breaks an observable assertion.
    index=0
    for h in range(7,21):
        for w in range(7,21):
            for n in range(2,6):
                grid=gen.generate(20261005,index,difficulty=band,grid_h=h,grid_w=w,palette_size=n)
                index+=1
                assert gen.observe_overrides(grid)=={'grid_h':h,'grid_w':w,'palette_size':n}
                assert not gen.self_check(grid)
                stats=probe.domain_counts(grid)
                assert stats['collision_components']==0
                assert stats['seedless_components']>0
                assert stats['growing_seeded_components']==n
                expected=probe.oracle(grid)
                # Iterate actual declarations, rather than a copied name list.
                for namespace in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS','SEMANTIC_RIVALS'):
                    for name,rival in getattr(gen,namespace).items():
                        assert rival(grid)!=expected,(band,h,w,n,namespace,name)


@pytest.mark.parametrize('seed',range(20))
def test_small_five_seed_boundary_across_independent_seeds(seed):
    grid=gen.generate(seed,83,difficulty='medium',grid_h=7,grid_w=7,palette_size=5)
    assert not gen.self_check(grid)
    assert probe.domain_counts(grid)['growing_seeded_components']==5


def test_rotation_and_seed_palette_equivariance_of_domain():
    def rotate(g): return [list(row) for row in zip(*g[::-1])]
    mapping={0:0,5:5,1:9,2:8,3:7,4:6,6:4,7:3,8:2,9:1}
    def recolor(g): return [[mapping[v] for v in row] for row in g]
    for index in range(12):
        grid=gen.generate(713,index,difficulty='hard')
        for _ in range(4):
            assert not gen.self_check(grid)
            assert probe.oracle(rotate(grid))==rotate(probe.oracle(grid))
            assert probe.oracle(recolor(grid))==recolor(probe.oracle(grid))
            grid=rotate(grid)


def test_rivals_are_pure_and_canonical_shortcut_claims_are_true():
    import copy
    pairs=canonical_pairs(TASK,root=find_root(__file__),labeled_only=True)
    for namespace in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS','SEMANTIC_RIVALS'):
        for name,rival in getattr(gen,namespace).items():
            for pair in pairs:
                grid=copy.deepcopy(pair['input']); before=copy.deepcopy(grid)
                prediction=rival(grid)
                assert grid==before
                assert prediction==rival(grid)
                if namespace=='CANONICAL_SHORTCUTS':
                    assert prediction==pair['output'],name


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_common_seed_scalar_is_strict(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0, difficulty="medium")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_common_sample_index_scalar_is_strict(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, sample_index, difficulty="medium")


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_common_difficulty_scalar_is_strict(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty)
