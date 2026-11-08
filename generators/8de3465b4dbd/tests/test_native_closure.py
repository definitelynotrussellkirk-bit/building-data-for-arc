"""Literal topology witnesses and native contract checks."""
from pathlib import Path
import copy, hashlib, importlib.util, json, random
import pytest
from reviewer_support import find_root
ROOT=find_root(__file__)
HOME=ROOT/'generators/8de3465b4dbd/workspace/parametric'

@pytest.fixture(scope='module')
def native():
    path=HOME/'native.py'
    assert path.is_file(), 'native triggered-closure family is missing'
    spec=importlib.util.spec_from_file_location('tested_native_closure',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def fixture():
    # First enclosure closes via one exact horizontal gate; the second was
    # already closed. The third has a reverse gate and must remain open.
    g=[[0]*19 for _ in range(7)]
    for c0 in (1,7,13):
        for r in range(1,6):
            for c in range(c0,c0+5):
                if r in (1,5) or c in (c0,c0+4): g[r][c]=3
    g[1][1:4]=[2,3,0]
    g[1][13:16]=[3,2,0]
    want=copy.deepcopy(g);want[1][3]=8
    for r in range(2,5):
        for c in range(2,5): want[r][c]=4
    return g,want


def test_fill_newly_sealed_only_not_preclosed_or_reverse(native):
    g,want=fixture();original=copy.deepcopy(g)
    assert native.predict(g,'newly_enclosed')==want
    assert native.predict(g,'all_enclosed')!=want
    assert native.predict(g,'enclosed_before')!=want
    assert g==original


def test_two_gates_require_both_to_close(native):
    g,want=fixture()
    g[5][1:4]=[3,2,0]
    expected=copy.deepcopy(g);expected[1][3]=8
    assert native.predict(g,'newly_enclosed')==expected
    g[5][1:4]=[2,3,0]
    want[5][1:4]=[2,3,8]
    assert native.predict(g,'newly_enclosed')==want


def test_exact_default_and_protected_racket_hand_witnesses(native):
    from arc_repl import racket_bridge
    from arcpuzzles.parametric_worker import _real_evaluator
    assert hashlib.sha256(native.program({'closure_policy':'markers_only'}).encode()).hexdigest()=='b3679e3b614ff63c5de6099ccf1013863a0d14456968b052874d8331d7f761ab'
    runtime=Path(racket_bridge.__file__).resolve().parents[1]
    assert runtime in (ROOT,ROOT/'shared/runtime')
    apply,identity,bridge=_real_evaluator(runtime)
    try:
        assert identity['protected']
        g,want=fixture()
        assert apply(native.program({'closure_policy':'newly_enclosed'}),g)==want
        for rule in native.SETTINGS+native.RIVALS:
            assert apply(native.rule_for(rule),g)==native.predict(g,rule), rule
    finally: bridge.close()


def test_count_prefix_matched_grammar_and_private_shuffle(native):
    rngstate=random.getstate();orders=set()
    for seed in (0,1,7,17):
        whole=native.generate(seed,{'closure_policy':'newly_enclosed'},6,4)
        base=native.generate(seed,{'closure_policy':'markers_only'},2,1)
        assert [p['input'] for p in whole['train'][:2]]==[p['input'] for p in base['train']]
        assert whole['test'][0]['input']==base['test'][0]['input']
        assert len({json.dumps(p['input']) for p in whole['train']+whole['test']})==10
        orders.add(tuple(whole['private']['query_source_indices']))
        for i in range(4):
            assert native.public_turn(whole,i)=={'train':whole['train'],'test':[{'input':whole['test'][i]['input']}]}
        g=next(p['input'] for p in whole['test'] if len(p['input'])==30)
        obs=native.observe(g)
        assert obs['new_regions']>=3 and obs['old_regions']>=1
        cells=[(r,c) for r in range(30) for c in range(30) if g[r][c]]
        assert len(cells)>150
        assert {(r//15,c//15) for r,c in cells}=={(0,0),(0,1),(1,0),(1,1)}
        assert min(r for r,c in cells)==0 and max(r for r,c in cells)==29
        assert min(c for r,c in cells)==0 and max(c for r,c in cells)==29
    assert len(orders)>1
    assert rngstate==random.getstate()


def test_two_demo_teaching_and_constructed_room_oracle(native):
    for seed in range(10):
        ep=native.generate(seed,{'closure_policy':'newly_enclosed'},2,4)
        for rival in native.RIVALS:
            assert any(native.predict(p['input'],rival)!=p['output'] for p in ep['train']), (seed,rival)
        for slot in range(10):
            g,expected=native.construct(seed,slot)
            result=native.predict(g,'newly_enclosed')
            actual={(r,c) for r,row in enumerate(result) for c,x in enumerate(row) if x==4}
            assert actual==set(map(tuple,expected)), (seed,slot)


@pytest.mark.parametrize('args', [(-1,{},2,4),(True,{},2,4),(0,{'closure_policy':'bad'},2,4),(0,{'closure_policy':'markers_only','unknown':1},2,4),(0,{'closure_policy':'markers_only'},1,4),(0,{'closure_policy':'markers_only'},7,4),(0,{'closure_policy':'markers_only'},2,0),(0,{'closure_policy':'markers_only'},2,5),(0,{'closure_policy':'markers_only'},2,True)])
def test_invalid_requests(native,args):
    with pytest.raises(ValueError): native.generate(*args)
