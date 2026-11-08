"""Behavioral tests of packing, ordering, original labels and public boundaries."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1]

def load():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(),'native adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('_2ba387bc_test_adapter',p)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def test_base_generator_accepts_optional_difficulty():
    spec=importlib.util.spec_from_file_location('_2ba387bc_worker_contract',HOME/'generator.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    for seed,index in ((17,0),(43,1)):
        assert m.generate(seed,index,difficulty=None)==m.generate(seed,index,difficulty='medium')
        assert m.self_check(m.generate(seed,index))==[]
    with pytest.raises(ValueError):m.generate(17,0,difficulty='unknown')

def originals():
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['2ba387bc']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['2ba387bc']
    return d['train']+[dict(input=p['input'],output=gold[i]) for i,p in enumerate(d['test'])]

@pytest.mark.parametrize('index',range(5))
def test_general_python_rule_matches_originals(index):
    p=originals()[index];assert load().model.solve(p['input'],'row')==p['output']

def test_reference_resource_is_exact():
    assert load().program({'order_axis':'row'})==(HOME/'reference.rkt').read_text()

@pytest.mark.parametrize('mode',['row','column'])
def test_two_demonstrations_teach_axis_and_queries_are_novel(mode):
    a=load();e=a.generate(17,{'order_axis':mode},2,4)
    assert len(e['train'])==2 and len(e['test'])==4
    assert len({json.dumps(p['input']) for p in e['train']+e['test']})==6
    other='column' if mode=='row' else 'row'
    assert any(a.model.solve(p['input'],other)!=p['output'] for p in e['train'])

def test_public_view_is_one_query_and_excludes_private_metadata():
    a=load();e=a.generate(17,{'order_axis':'row'},2,4);v=a.public_view(e,0)
    assert v=={'train':e['train'],'test':[{'input':e['test'][0]['input']}]}
    e['seed']=123;e['program_solution']='secret';e['test'][0]['output']=[[9]];e['test'][1]['input']=[[8]]
    assert a.public_view(e,0)==v

@pytest.fixture(scope='module')
def racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()

@pytest.mark.parametrize('index',range(5))
def test_protected_racket_matches_every_original_label(index,racket):
    a=load();p=originals()[index]
    assert racket(a.program({'order_axis':'row'}),p['input'])==p['output']

@pytest.mark.parametrize('seed',[0,17,43])
def test_generated_labels_match_racket_both_settings(seed,racket):
    a=load()
    for mode in a.model.MODES:
        e=a.generate(seed,{'order_axis':mode},2,4)
        for p in e['train']+e['test']:assert racket(e['program_solution'],p['input'])==p['output']

@pytest.mark.parametrize('settings',[{}, {'order_axis':True},{'order_axis':'unknown'},{'order_axis':'row','extra':0},None])
def test_unknown_settings_fail_closed(settings):
    with pytest.raises(ValueError):load().program(settings)

@pytest.mark.parametrize('d,q',[(True,4),(2,False),(1,4),(7,4),(2,0),(2,5),(2.0,4)])
def test_bad_counts_are_rejected(d,q):
    with pytest.raises(ValueError):load().generate(17,{'order_axis':'row'},d,q)

@pytest.mark.parametrize('seed',range(8))
def test_setting_blind_prefix_stability(seed):
    a=load();full=a.generate(seed,{'order_axis':'row'},6,4)
    for d,q in ((2,1),(3,4),(6,2)):
        e=a.generate(seed,{'order_axis':'row'},d,q)
        assert e['train']==full['train'][:d] and e['test']==full['test'][:q]
    other=a.generate(seed,{'order_axis':'column'},6,4)
    for split in ('train','test'):assert [p['input'] for p in full[split]]==[p['input'] for p in other[split]]
    assert len({json.dumps(p['input']) for p in full['train']+full['test']})==10

@pytest.mark.parametrize('seed',range(8))
def test_stress_and_two_sided_padding(seed):
    a=load();g=a.model.sample_input(seed,3,query=True);st=a.model.infer(g)
    assert len(g)==len(g[0])==30 and len(st['blocks'])==9
    assert sum(v!=st['background'] for row in g for v in row)>=190
    assert len(a.model.solve(g,'row'))==30
    assert any(v!=st['background'] for v in g[0]) and any(v!=st['background'] for v in g[-1])
    assert any(row[0]!=st['background'] for row in g) and any(row[-1]!=st['background'] for row in g)
    e=a.generate(seed,{'order_axis':'row'},2,4)
    differences=[]
    for p in e['train']:
        state=a.model.infer(p['input']);b=a.model.ordered_buckets(state,'row')
        differences.append(len(b[0])-len(b[1]))
    assert min(differences)<0<max(differences)

@pytest.mark.parametrize('g',[[],[[True]],[[0,1],[0]],[[0]*31],[[0,0],[0,0]]])
def test_bad_or_unstructured_inputs_fail_closed(g):
    with pytest.raises(ValueError):load().model.solve(g)


def test_ordinary_generator_returns_grid_and_empty_findings():
    spec=importlib.util.spec_from_file_location('_2ba387bc_base_test',HOME/'generator.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    g=m.generate(seed=17,sample_index=0,difficulty='medium')
    assert type(g) is list and m.self_check(g)==[]
    with pytest.raises(ValueError):m.generate(seed=True)
    with pytest.raises(ValueError):m.generate(unknown=1)


def test_minimum_lesson_refutes_six_block_budget_not_only_query():
    a=load()
    for mode in a.model.MODES:
        e=a.generate(17,{'order_axis':mode},2,4)
        def budget(g):
            state=a.model.infer(g);state['blocks']=state['blocks'][:6]
            return a.model.render(state,a.model.ordered_buckets(state,mode))
        assert any(budget(p['input'])!=p['output'] for p in e['train'])
