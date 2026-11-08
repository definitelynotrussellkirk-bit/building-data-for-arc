from pathlib import Path
import importlib.util, json, random, copy
import pytest
HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'
def load(name):
    p=BASE/(name+'.py');assert p.is_file(),f'missing implementation {name}'
    s=importlib.util.spec_from_file_location('_chain_test_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('i',range(5))
def test_original_labels(i):
    p=json.loads((HOME/'tests/originals.json').read_text())[i]
    assert load('engine').predict(p['input'],'canonical')==p['output']

@pytest.mark.parametrize('i,axis,order',[(0,'vertical',[0,3,1,2]),(1,'horizontal',[2,1,0]),(2,'vertical',[0,1,2]),(3,'horizontal',[2,3,1,0]),(4,'vertical',[3,1,2,0])])
def test_original_contact_order(i,axis,order):
    p=json.loads((HOME/'tests/originals.json').read_text())[i];cert=load('engine').parse(p['input'])
    assert cert['axis']==axis and cert['order']==order

@pytest.mark.parametrize('d',range(2,7))
@pytest.mark.parametrize('q',range(1,5))
def test_count_prefix_contract(d,q):
    a=load('adapter');full=a.generate(17,{'counting':'prefix_parity'},6,4);short=a.generate(17,{'counting':'prefix_parity'},d,q)
    assert short['train']==full['train'][:d] and short['test']==full['test'][:q]
    assert a.public_turn(short)==a.public_turn(a.generate(17,{'counting':'prefix_parity'},d,1))

@pytest.mark.parametrize('seed',[0,1,17,43])
def test_matched_settings_and_rng(seed):
    a=load('adapter');before=random.getstate();r=a.generate(seed,{'counting':'canonical'},2,4);s=a.generate(seed,{'counting':'prefix_parity'},2,4)
    assert random.getstate()==before
    assert [p['input'] for sp in ('train','test') for p in r[sp]]==[p['input'] for sp in ('train','test') for p in s[sp]]
    assert any(x['output']!=y['output'] for x,y in zip(r['train'],s['train']))
    assert any(len(p['input'])==len(p['input'][0])==30 for p in s['test'])
    assert len({json.dumps(p['input']) for sp in ('train','test') for p in s[sp]})==6

@pytest.mark.parametrize('bad',[[],[[True]],[[1.0]],[[10]],[[0],[1,2]],[[7]*31]*2,[[7,7],[7,7]],[[6]*5]*5])
def test_bad_grids_rejected(bad):
    with pytest.raises(ValueError):load('engine').predict(bad,'canonical')

def test_program_closure_and_generator_drift():
    a=load('adapter');assert a.program({'counting':'canonical'})==(HOME/'reference.rkt').read_text()==(BASE/'canonical.rkt').read_text()
    assert load('build_generator').source()==(HOME/'generator.py').read_text()

@pytest.mark.parametrize('args',[(True,{'counting':'canonical'},2,4),(0,{},2,4),(0,{'counting':'bad'},2,4),(0,{'counting':'canonical'},1,4),(0,{'counting':'canonical'},2,0),(0,{'counting':'canonical'},2,5),(0,{'counting':'canonical'},True,1)])
def test_contract_rejects_bad_arguments(args):
    with pytest.raises(ValueError):load('adapter').generate(*args)

def test_metadata_and_public_mutation_isolation():
    a=load('adapter');e=a.generate(17,{'counting':'prefix_parity'},2,4);before=copy.deepcopy(e);v=a.public_turn(e)
    e['private'].clear();v['train'][0]['input'][0][0]=9
    assert a.generate(17,{'counting':'prefix_parity'},2,4)==before

def test_retained_color_sort_hole_and_repaired_minimum_lesson():
    a=load('adapter');old=json.loads((HOME/'tests/color-shortcut-before.json').read_text())
    assert all(a.predict(p['input'],'color_sort')==p['output'] for p in old['train'])
    assert a.predict(old['test'][0]['input'],'color_sort')!=old['test'][0]['output']
    new=a.generate(48,{'counting':'canonical'},2,4)
    assert any(a.predict(p['input'],'color_sort')!=p['output'] for p in new['train'])

def test_query_bank_has_same_color_panels():
    a=load('adapter');ep=a.generate(43,{'counting':'canonical'},2,4)
    assert any(len({v for t in a.parse(p['input'])['tiles'] for row in t for v in row if v!=7})==1 for p in ep['test'])

def test_whole_contact_sets_not_single_shared_port():
    a=load('adapter');p=a.generate(17,{'counting':'canonical'},2,4)['train'][0];e=load('engine');c=e.parse(p['input'])
    assert len(e._chains(c['tiles']))==1
    assert len(e._chains(c['tiles'],'overlap'))>1
    assert e.predict(p['input'],'overlap')!=p['output']

def test_black_is_foreground_not_background():
    e=load('engine');p=json.loads((HOME/'tests/originals.json').read_text())[0]
    change=lambda g:[[0 if v==2 else v for v in row] for row in g]
    assert e.predict(change(p['input']),'canonical')==change(p['output'])

def test_ambiguous_complete_chain_is_rejected():
    e=load('engine')
    head=[[7]*3,[7,2,7],[7,2,7]]
    middle=[[7,2,7]]*3
    tail=[[7,2,7],[7,2,7],[7]*3]
    ambiguous=e._pack([head,middle,middle,tail],4,1,1)
    with pytest.raises(ValueError,match='unique'):e.parse(ambiguous)

def test_reusable_color_sort_counterfactual_changes_only_order_definition():
    a=load('adapter');r=load('replay_color_shortcut');correct=a.program(a.DEFAULT);wrong=r.color_sorted_program(a)
    assert correct!=wrong
    assert '(define count-policy "canonical")' in wrong
    assert '(define prefix-scope "assembled")' in wrong
