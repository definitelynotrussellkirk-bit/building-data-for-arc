from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest
from reviewer_support import find_root

ROOT = find_root(Path(__file__))
HOME = ROOT / 'generators/public_eval_20270e3b'

def load(name, path):
    assert path.is_file(), f'Missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def gen():
    return load('20270e3b_generator_test', HOME/'generator.py')

@pytest.fixture
def adapter():
    return load('20270e3b_adapter_test', HOME/'workspace/parametric/adapter.py')

def original_pairs():
    challenges = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['20270e3b']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['20270e3b']
    grid = lambda g: [[int(v) for v in row] for row in g]
    return [(grid(p['input']), grid(p['output'])) for p in challenges['train']] + [(grid(p['input']), grid(o)) for p,o in zip(challenges['test'],gold)]

@pytest.mark.parametrize('index',range(6))
def test_original_labels(gen,index):
    inp,out=original_pairs()[index]
    assert gen.solve(inp) == out
    assert gen.self_check(inp) == []

@pytest.mark.parametrize('mode',['canonical','enclosed_fill_relay'])
@pytest.mark.parametrize('demos',range(2,7))
@pytest.mark.parametrize('queries',range(1,5))
def test_counts_prefixes_matched_inputs(adapter,gen,mode,demos,queries):
    s={'mode':mode}; e=adapter.generate(17,s,demos,queries); f=adapter.generate(17,s,6,4)
    assert len(e['train'])==demos and len(e['test'])==queries
    assert e['train']==f['train'][:demos] and e['test']==f['test'][:queries]
    assert e['program_solution']==adapter.program(s)
    other=adapter.generate(17,{'mode':'canonical'},demos,queries)
    for split in ('train','test'):
        assert [p['input'] for p in e[split]] == [p['input'] for p in other[split]]
        for p in e[split]:
            assert gen.self_check(p['input']) == []
            assert p['output'] == gen.solve(p['input'],mode)
    inputs=[json.dumps(p['input']) for sp in ('train','test') for p in e[sp]]
    assert len(set(inputs)) == len(inputs)

@pytest.mark.parametrize('seed',[0,1,17,43,103])
def test_minimum_teaching_and_boundary(adapter,gen,seed):
    e=adapter.generate(seed,{'mode':'enclosed_fill_relay'},2,4)
    assert any(gen.solve(p['input']) != p['output'] for p in e['train'])
    assert any(len(p['input'])==len(p['input'][0])==30 for p in e['test'])
    big=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    assert sum(v in (4,7) for row in big['input'] for v in row) > 150
    assert max(len(big['output']),len(big['output'][0]))==30
    assert any(v==8 for row in big['output'] for v in row)
    failures=gen.teaching_failures(e,'enclosed_fill_relay')
    assert failures == []

@pytest.mark.parametrize('bad',[[[True]],[[1.0]],[[10]],[[-1]],[],[[]],[[0],[0,1]],[[0]*31]])
def test_invalid_grid(gen,bad):
    with pytest.raises(ValueError): gen.solve(bad)
    assert gen.self_check(bad)

@pytest.mark.parametrize('settings',[{}, {'mode':'bad'},{'mode':True},{'mode':'canonical','extra':1}])
def test_invalid_settings(adapter,settings):
    with pytest.raises(ValueError): adapter.program(settings)

@pytest.mark.parametrize('demos,queries',[(1,4),(7,4),(True,4),(2,0),(2,5),(2,True),(2,1.0)])
def test_invalid_counts(adapter,demos,queries):
    with pytest.raises(ValueError): adapter.generate(0,{'mode':'canonical'},demos,queries)

def test_default_exact_and_no_global_rng(adapter):
    assert adapter.program({'mode':'canonical'})==(HOME/'reference.rkt').read_text()
    before=random.getstate(); s={'mode':'canonical'}
    e=adapter.generate(9,s,2,4)
    assert random.getstate()==before and s=={'mode':'canonical'}
    assert e==adapter.generate(9,s,2,4)

def test_public_first_turn_and_private_invariance(adapter):
    e=adapter.generate(43,{'mode':'enclosed_fill_relay'},3,4)
    one=adapter.generate(43,{'mode':'enclosed_fill_relay'},3,1)
    visible=adapter.public_bytes(e,0)
    assert visible==adapter.public_bytes(one,0)
    changed=copy.deepcopy(e)
    changed['program_solution']='secret';changed['settings']={'secret':True}
    for pair in changed['test']: pair['output']={'secret':True}
    changed['test'][1:]=[{'invalid_future':True}]
    assert adapter.public_bytes(changed,0)==visible
    assert json.loads(visible)=={'train':e['train'],'test':[{'input':e['test'][0]['input']}]}
    changed['test'][0]['input'][0][0]=(changed['test'][0]['input'][0][0]+1)%10
    assert adapter.public_bytes(changed,0)!=visible

def test_presentation_not_fixed(adapter):
    orders={tuple(adapter.generate(i,{'mode':'canonical'},2,4)['query_source_indices']) for i in range(16)}
    assert len(orders)>5
    assert any(o[0]!=0 for o in orders)

def test_verifier_rejects_stale_source(tmp_path):
    import hashlib
    verify=load('20270e3b_verify_test',HOME/'workspace/parametric/verify.py')
    source=tmp_path/'source.py';source.write_text('a=1\n')
    binding={'files':[{'path':'source.py','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]}
    verify.check_binding(tmp_path,binding)
    source.write_text('a=2\n')
    with pytest.raises(ValueError,match='Source binding'): verify.check_binding(tmp_path,binding)

@pytest.mark.parametrize('index',range(6))
def test_whole_port_patterns_are_cardinally_adjacent(gen,index):
    inp,_=original_pairs()[index];d=gen.decode(inp)
    moved=gen.shift(d['b_marks'],d['delta'])
    assert any(moved==gen.shift(d['a_marks'],normal) for normal in ((-1,0),(1,0),(0,-1),(0,1)))

def test_racket_skips_overwide_alignment_at_arc_boundary(gen,adapter):
    """Two geometric dockings exist, but only one stays within 30 columns."""
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    g=[[1]*30 for _ in range(27)]
    for r in range(14):g[r][29]=4
    for c in range(14,29):g[14][c]=4
    g[14][29]=7
    for r in range(13,27):g[r][0]=4
    for c in range(1,16):g[12][c]=4
    g[12][0]=7
    assert gen.self_check(g)==[]
    expected=gen.solve(g)
    assert len(expected[0])==30
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for mode in gen.MODES:
                assert apply(adapter.program({'mode':mode}),g)==gen.solve(g,mode)
        finally:bridge.close()
