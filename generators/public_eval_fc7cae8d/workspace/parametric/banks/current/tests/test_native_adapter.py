import copy
import importlib.util
import random
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fc7_adapter_test',HOME/'workspace/parametric/adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)


def test_minimum_demos_identify_both_settings_and_canonical_bytes():
    assert A.program({'marker_pairing':'match'})==(HOME/'reference.rkt').read_text()
    for seed in (0,17,43,2**63-1):
        left=A.generate(seed,{'marker_pairing':'match'},2,4)
        right=A.generate(seed,{'marker_pairing':'swap'},2,4)
        assert [p['input'] for sp in ('train','test') for p in left[sp]]==[p['input'] for sp in ('train','test') for p in right[sp]]
        assert any(a['output']!=b['output'] for a,b in zip(left['train'],right['train']))
        assert all(a['output']!=b['output'] for a,b in zip(left['test'],right['test']))


def test_counts_prefixes_no_aliases_or_global_random_mutation():
    before=random.getstate()
    for pairing in ('match','swap'):
        setting={'marker_pairing':pairing};original=copy.deepcopy(setting)
        full=A.generate(17,setting,6,4)
        for demos in range(2,7):
            for queries in range(1,5):
                lesson=A.generate(17,setting,demos,queries)
                assert lesson['train']==full['train'][:demos]
                assert lesson['test']==full['test'][:queries]
                assert set(lesson)=={'train','test','program_solution'}
        assert setting==original
        full['train'][0]['input'][0][0]=-7
        assert A.generate(17,setting,6,4)['train'][0]['input'][0][0]>=0
    assert random.getstate()==before


@pytest.mark.parametrize('pairing',['match','swap'])
def test_two_demos_refute_inverse_orientation(pairing):
    # Regression: seed9/match originally taught only reflection and half-turn.
    # Those are their own inverses, although a later quarter-turn query differs.
    for seed in (9,0,17,43,2**63-1,*range(32)):
        setting={'marker_pairing':pairing};lesson=A.generate(seed,setting,2,4)
        inverse_labels=[]
        for pair in lesson['train']:
            frame=A.family.inspect_grid(pair['input'])
            k=A.family.transform_index(frame,setting)
            inverse={1:3,3:1}.get(k,k)
            inverse_labels.append(A.family.transform_grid(frame['picture'],inverse))
        assert any(pair['output']!=wrong for pair,wrong in zip(lesson['train'],inverse_labels)), (seed,pairing)


def test_two_demos_share_shapes_and_require_different_transformations():
    for seed in (0,9,17,43,2**63-1):
        lesson=A.generate(seed,{'marker_pairing':'match'},2,4)
        grids=[p['input'] for p in lesson['train']]
        frames=[A.family.inspect_grid(g) for g in grids]
        assert (len(grids[0]),len(grids[0][0]))==(len(grids[1]),len(grids[1][0]))
        pictures=[f['picture'] for f in frames]
        assert (len(pictures[0]),len(pictures[0][0]))==(len(pictures[1]),len(pictures[1][0]))
        assert A.family.transform_index(frames[0],{'marker_pairing':'match'})!=A.family.transform_index(frames[1],{'marker_pairing':'match'})


@pytest.mark.parametrize('seed',[True,-1,2**63,0.0,'0',None])
def test_bad_seeds(seed):
    with pytest.raises((ValueError,TypeError)):A.generate(seed,{'marker_pairing':'match'},2,4)


@pytest.mark.parametrize('demos,queries',[(True,4),(1,4),(7,4),(2.0,4),(2,True),(2,0),(2,5),(2,4.0)])
def test_bad_counts(demos,queries):
    with pytest.raises((ValueError,TypeError)):A.generate(0,{'marker_pairing':'match'},demos,queries)


@pytest.mark.parametrize('setting',[{},None,[],{'marker_pairing':True},{'marker_pairing':'swap','extra':0}])
def test_bad_settings(setting):
    with pytest.raises((ValueError,TypeError)):A.generate(0,setting,2,4)
