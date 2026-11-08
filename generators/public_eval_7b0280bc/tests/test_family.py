"""Regressions: original labels, occlusion, zero-only holes, connectivity, privacy."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load(path, name):
    assert path.is_file(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def model():
    return load(HOME/'generator.py', '_path_generator')

@pytest.fixture(scope='module')
def adapter():
    return load(HOME/'workspace/parametric/adapter.py', '_path_adapter')

def originals():
    pid='7b0280bc'
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())[pid]
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())[pid]
    return data['train']+[dict(input=p['input'],output=o) for p,o in zip(data['test'],gold)]

def test_references_exist():
    assert (HOME/'reference.rkt').is_file(), 'general Racket rule is missing'

@pytest.mark.parametrize('index',range(4))
def test_original_labels(model,index):
    p=originals()[index]
    assert model.solve(p['input'],'fewest_edges') == p['output']

@pytest.mark.parametrize('seed',[0,17,43])
@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_matched_inputs_prefix_stability(adapter,seed,demos):
    one=adapter.generate(seed,{'route_metric':'fewest_edges'},demos,1)
    all_=adapter.generate(seed,{'route_metric':'fewest_edges'},demos,4)
    alt=adapter.generate(seed,{'route_metric':'least_ink'},demos,4)
    assert len(all_['train'])==demos and len(all_['test'])==4
    assert one['test']==all_['test'][:1]
    assert one['train']==all_['train']
    assert [p['input'] for p in all_['train']+all_['test']]==[p['input'] for p in alt['train']+alt['test']]
    assert any(a['output']!=b['output'] for a,b in zip(all_['train'],alt['train']))
    assert all(a['output']!=b['output'] for a,b in zip(all_['test'],alt['test']))
    keys=[json.dumps(p['input']) for p in all_['train']+all_['test']]
    assert len(keys)==len(set(keys))
    assert len(all_['test'][3]['input'])==len(all_['test'][3]['input'][0])==30
    for pair in all_['train']+all_['test']+alt['train']+alt['test']:
        for g in pair.values():
            assert 1<=len(g)<=30 and 1<=len(g[0])<=30
            assert all(len(row)==len(g[0]) for row in g)
            assert all(type(v) is int and 0<=v<=9 for row in g for v in row)

@pytest.mark.parametrize('kwargs',[
    dict(seed=True),dict(seed=-1),dict(seed=2.0),dict(demos=True),dict(demos=1),dict(demos=7),
    dict(queries=0),dict(queries=5),dict(queries=2.0),dict(settings={'route_metric':True}),
    dict(settings={'route_metric':'fewest_edges','unknown':0}),dict(settings={}),dict(settings=None)])
def test_adapter_strict_controls(adapter,kwargs):
    args=dict(seed=0,settings={'route_metric':'fewest_edges'},demos=2,queries=4);args.update(kwargs)
    with pytest.raises(ValueError):adapter.generate(**args)

@pytest.mark.parametrize('kwargs',[dict(seed=True),dict(seed=-1),dict(sample_index=-1),dict(sample_index='1'),dict(foo=3),dict(grid_h=10),dict(grid_w=True),dict(difficulty='fake')])
def test_generator_strict_controls(model,kwargs):
    args=dict(seed=0,sample_index=0);args.update(kwargs)
    with pytest.raises(ValueError):model.generate(**args)

def test_canonical_and_runtime_copies_match(adapter):
    assert adapter.program({'route_metric':'fewest_edges'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/kernel.py').read_bytes()

def test_route_metrics_and_lexicographic_ties(model):
    graph={'nodes':[{} for _ in range(5)],'endpoints':[0,4],
           'edges':[{'nodes':(0,1),'cells':[(0,i) for i in range(10)]},
                    {'nodes':(1,4),'cells':[(1,i) for i in range(10)]},
                    {'nodes':(0,2),'cells':[(2,0)]},
                    {'nodes':(2,3),'cells':[(3,0)]},
                    {'nodes':(3,4),'cells':[(4,0)]}]}
    assert model.choose_route(graph,'fewest_edges')['nodes']==[0,1,4]
    assert model.choose_route(graph,'least_ink')['nodes']==[0,2,3,4]
    # Equal-cost paths resolve by complete node reading-order sequence.
    graph['edges'][0]['cells']=[(0,0)];graph['edges'][1]['cells']=[(1,0)]
    assert model.choose_route(graph,'least_ink')['nodes']==[0,1,4]

def test_self_check_rejects_malformed(model):
    for g in ([],[[1],[1,2]],[[True]],[[10]],[[0]*40]):
        assert model.self_check(g)

@pytest.mark.parametrize('seed',range(8))
def test_sampler_census(model,seed):
    for index in range(10):
        g=model.generate(seed,index)
        assert not model.self_check(g)
        assert g==model.generate(seed,index)
        assert (model.solve(g,'fewest_edges')==model.solve(g,'least_ink')) == (index%7==1)

def test_relocated_generator_self_contained(model,tmp_path):
    target=tmp_path/'generator.py';target.write_bytes((HOME/'generator.py').read_bytes())
    code="import generator; g=generator.generate(17,3); assert not generator.self_check(g); print(len(g))"
    run=subprocess.run([sys.executable,'-I','-c',f"import sys;sys.path.insert(0,{str(tmp_path)!r});"+code],capture_output=True,text=True)
    assert run.returncode==0,run.stderr

def test_public_view_private_invariance_and_shuffle(adapter):
    e=adapter.generate(17,{'route_metric':'fewest_edges'},2,4)
    modified=copy.deepcopy(e);modified['settings']={'LEAK':1};modified['program_solution']='LEAK'
    for p in modified['test']:p['output']=[[9]]
    firsts=set()
    for seed in range(12):
        a=adapter.public_turns(e,seed);b=adapter.public_turns(modified,seed)
        assert a==b and len(a)==4
        assert all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in a)
        firsts.add(json.dumps(a[0]['test'][0]['input']))
    assert len(firsts)>1

@pytest.fixture(scope='module')
def racket():
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:yield apply
        finally:bridge.close()

def test_protected_originals(racket):
    source=(HOME/'reference.rkt').read_text()
    for p in originals():assert racket(source,p['input'])==p['output']

@pytest.mark.parametrize('scope',['fewest_edges','least_ink'])
def test_protected_every_profile(adapter,racket,scope):
    e=adapter.generate(17,{'route_metric':scope},6,4)
    for p in e['train']+e['test']:
        assert racket(e['program_solution'],p['input'])==p['output']

@pytest.fixture(scope='module')
def audit_tool():
    return load(HOME/'workspace/parametric/audit.py','_path_audit')

def test_source_binding_rejects_drift(audit_tool,tmp_path):
    import hashlib
    f=tmp_path/'source.py';f.write_text('old')
    receipt={'source_binding':{'files':[{'path':'source.py','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]}}
    audit_tool.check_binding(tmp_path,receipt)
    f.write_text('new')
    with pytest.raises(ValueError):audit_tool.check_binding(tmp_path,receipt)

def test_public_bundle_rejects_duplicate_views(adapter,audit_tool,tmp_path):
    episode=adapter.generate(17,{'route_metric':'fewest_edges'},2,4)
    entries=[{'seed':17,'settings':{'route_metric':'fewest_edges'},**episode}]*2
    with pytest.raises(ValueError):audit_tool.write_public_bundle(entries,tmp_path/'bad')
    assert not (tmp_path/'bad').exists()

def test_public_bundle_ids_hash_exact_visible_bytes(adapter,audit_tool,tmp_path):
    import hashlib
    episode=adapter.generate(17,{'route_metric':'fewest_edges'},2,4)
    report=audit_tool.write_public_bundle([{'seed':17,'settings':{'route_metric':'fewest_edges'},**episode}],tmp_path/'ok')
    assert report['views']==4
    for f in (tmp_path/'ok/public').glob('*.json'):
        assert f.stem==hashlib.sha256(f.read_bytes()).hexdigest()
        value=json.loads(f.read_text());assert set(value)=={'train','test'} and len(value['test'])==1


@pytest.mark.parametrize('seed',[0,17,43])
def test_diagonal_pipe_and_dead_branch_teaching(model,seed):
    g=model.generate(seed,0,grid_h=18,grid_w=20)
    graph=model.analyze(g)
    # Some eight-connected segment would split if a solver used four-connectivity.
    assert any(len(model.components(e['cells'],diagonal=False))>1 for e in graph['edges'])
    degree=[sum(i in e['nodes'] for e in graph['edges']) for i in range(len(graph['nodes']))]
    assert any(d==1 and i not in graph['endpoints'] for i,d in enumerate(degree))

def test_curriculum_varies_route_node_counts(model):
    counts={'fewest_edges':set(),'least_ink':set()}
    for i in range(6):
        graph=model.analyze(model.generate(17,i,grid_h=24,grid_w=26))
        for metric in counts:counts[metric].add(len(model.choose_route(graph,metric)['nodes'])-2)
    assert len(counts['fewest_edges'])>=2, 'a fixed one-middle-node rule must not fit the curriculum'
    assert len(counts['least_ink'])>=3, 'the physical route must have varying node count'

@pytest.mark.parametrize('seed',[0,17,43])
def test_two_demo_curriculum_refutes_longest_ink_shortcut(model,seed):
    graph0=model.analyze(model.generate(seed,0,grid_h=18,grid_w=20))
    graph1=model.analyze(model.generate(seed,1,grid_h=21,grid_w=19))
    assert model.choose_route(graph0,'fewest_edges')['nodes']!=model.choose_route(graph0,'least_ink')['nodes']
    assert model.choose_route(graph1,'fewest_edges')['nodes']==model.choose_route(graph1,'least_ink')['nodes']

@pytest.mark.parametrize('seed',[0,17,43])
def test_two_demo_lessons_reject_route_position_shortcuts(adapter,audit_tool,seed):
    for metric in ('fewest_edges','least_ink'):
        episode=adapter.generate(seed,{'route_metric':metric},2,4)
        predicted=[audit_tool.rivals(p['input'],metric) for p in episode['train']]
        for name in ('first_reading_order_path','last_reading_order_path','maximum_ink'):
            assert any(pred[name]!=p['output'] for pred,p in zip(predicted,episode['train'])),(seed,metric,name)
    agreement=adapter.generate(seed,{'route_metric':'fewest_edges'},2,4)['train'][1]['input']
    assert len(audit_tool.all_routes(audit_tool.model.analyze(agreement)))>=3
