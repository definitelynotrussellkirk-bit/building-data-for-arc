"""Native forward/inverse analogy contracts and protected runtime checks."""
import copy
import importlib.util
import json

import pytest
from arcpuzzles import Catalog
from arc_repl.parser import parse_all
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, canonical_pairs, public_challenge_bytes

ROOT=find_root(__file__)
HOME=ROOT/'generators/155cf6b30713/workspace/parametric'

@pytest.fixture(scope='module')
def adapter():
    assert (HOME/'adapter.py').is_file(), 'native relation-transfer adapter missing'
    spec=importlib.util.spec_from_file_location('native_analogy_test',HOME/'adapter.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a


def test_exact_canonical_and_complete_programs(adapter):
    sources={v['program_solution'] for v in Catalog(ROOT).get(adapter.TASK)['variants']
             if isinstance(v.get('program_solution'),str)}
    assert {adapter.program({'direction':'forward'})}==sources
    for s in [adapter.program({'direction':p}) for p in adapter.DIRECTIONS]+[adapter.counterfactual_program()]:
        assert len(parse_all(s))==1


@pytest.mark.parametrize('seed,demos,queries',[(True,3,4),(-1,3,4),(0.0,3,4),(0,True,4),(0,1,4),(0,7,4),(0,3,0),(0,3,5),(0,3,False)])
def test_exact_request_types_and_boundaries(adapter,seed,demos,queries):
    with pytest.raises((ValueError,TypeError)):
        adapter.generate(seed,{'direction':'forward'},demos,queries)


@pytest.mark.parametrize('settings',[{},None,{'direction':True},{'direction':'other'},{'direction':'forward','extra':0}])
def test_unknown_settings_fail_closed(adapter,settings):
    with pytest.raises((ValueError,TypeError)):
        adapter.program(settings)


def test_literal_forward_reverse_and_pass_through(adapter):
    # First panels show clockwise rotation and 1->2->3->1 color permutation.
    # Query unknown color 7 must survive. Expectations are hand-derived.
    a=[[1,0,0,0],[2,3,0,0],[0,0,0,0],[0,0,0,0]]
    b=[[0,0,3,2],[0,0,1,0],[0,0,0,0],[0,0,0,0]]
    q=[[1,7,0,0],[0,0,0,0],[0,0,2,0],[0,0,0,3]]
    g=[x+[5]+y+[5]+z for x,y,z in zip(a,b,q)]
    forward=[[0,0,0,2],[0,0,0,7],[0,3,0,0],[1,0,0,0]]
    reverse=[[0,0,0,2],[0,0,1,0],[7,0,0,0],[3,0,0,0]]
    assert adapter.predict(g,'forward')==forward
    assert adapter.predict(g,'inverse')==reverse
    assert adapter.infer(g)==('r1',{1:2,2:3,3:1})


def test_count_prefix_matched_inputs_and_real_30x30(adapter):
    for seed in range(12):
        full=adapter.generate(seed,{'direction':'forward'},6,4)
        inputs=[p['input'] for p in full['train']+full['test']]
        assert len({json.dumps(g) for g in inputs})==10
        for g in inputs:assert adapter.input_errors(g)==[]
        stress=full['test'][3]
        assert len(stress['input'])==len(stress['input'][0])==30
        assert len(stress['output'])==30 and len(stress['output'][0])==9
        assert sum(bool(v) for row in stress['input'] for v in row)>=300
        assert sum(bool(v) for row in stress['output'] for v in row)>=70
        assert all(stress['output'][r][c] for r,c in ((0,0),(0,8),(29,0),(29,8)))
        for direction in adapter.DIRECTIONS:
            ep=adapter.generate(seed,{'direction':direction},6,4)
            assert [p['input'] for p in ep['train']+ep['test']]==inputs
            for demos in range(2,7):
                for queries in (1,4):
                    smaller=adapter.generate(seed,{'direction':direction},demos,queries)
                    assert smaller['train']==ep['train'][:demos]
                    assert smaller['test']==ep['test'][:queries]


def test_two_demos_refute_finite_shortcuts(adapter):
    for seed in range(32):
        for direction in adapter.DIRECTIONS:
            ep=adapter.generate(seed,{'direction':direction},2,4)
            assert adapter.teaching_failures(ep)==[]


def test_public_projection_private_invariance(adapter):
    ep=adapter.generate(17,{'direction':'inverse'},3,4)
    single=adapter.generate(17,{'direction':'inverse'},3,1)
    want=adapter.public_turn(ep,0)
    assert want==adapter.public_turn(single,0)
    dirty=copy.deepcopy(ep);dirty['settings']={'direction':'SECRET'};dirty['program_solution']='SECRET'
    dirty['test'][0]['output']=[[9]];dirty['test'][1:]=[{'input':[[9]],'output':[[9]]}]
    dirty['train'][0]['private_metadata']='SECRET'
    assert adapter.public_turn(dirty,0)==want
    assert set(want)=={'train','test'} and len(want['test'])==1
    assert public_challenge_bytes(want)
    for bad in (True,-1,4):
        with pytest.raises((ValueError,TypeError)):adapter.public_turn(ep,bad)


def test_domain_rejects_inconsistent_and_noninvertible_maps(adapter):
    ep=adapter.generate(0,{'direction':'forward'},2,4)
    g=copy.deepcopy(ep['train'][0]['input'])
    w=(len(g[0])-2)//3
    for row in g:
        for c in range(w+1,2*w+1):
            if row[c]:row[c]=1
    assert adapter.input_errors(g)
    g=copy.deepcopy(ep['test'][3]['input']);g[0][-1]=0
    assert adapter.input_errors(g)


def test_protected_labels_canonical_and_alignment_ablation(adapter):
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        for pair in canonical_pairs(adapter.TASK,root=ROOT,labeled_only=True):
            assert adapter.execute(bridge,adapter.program({'direction':'forward'}),pair['input'])==pair['output']
        for direction in adapter.DIRECTIONS:
            ep=adapter.generate(17,{'direction':direction},2,4)
            for pair in ep['train']+ep['test']:
                assert adapter.execute(bridge,ep['program_solution'],pair['input'])==pair['output']
        pair=adapter.generate(17,{'direction':'inverse'},2,4)['train'][0]
        assert adapter.execute(bridge,adapter.counterfactual_program(),pair['input'])!=pair['output']
