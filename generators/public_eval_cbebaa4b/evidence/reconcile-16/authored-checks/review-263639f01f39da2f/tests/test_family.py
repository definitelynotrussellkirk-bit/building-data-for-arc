from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter is missing'
    spec=importlib.util.spec_from_file_location('cbebaa4b_test_adapter',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def test_base_worker_generation_contract():
    from arcpuzzles.parametric_worker import _grid
    spec=importlib.util.spec_from_file_location('cbebaa4b_base_contract',HOME/'generator.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    samples=[module.generate(seed=17,sample_index=i,difficulty='medium') for i in range(4)]
    assert all(_grid(grid)==grid for grid in samples)
    assert len({json.dumps(grid) for grid in samples})==4
    assert samples[0]==module.generate(seed=17,sample_index=0,difficulty='medium')
    for kwargs in ({'sample_index':True},{'seed':False},{'difficulty':'unknown'},{'extra':1}):
        with pytest.raises(ValueError):module.generate(**kwargs)

def original_pairs():
    task=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['cbebaa4b']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['cbebaa4b']
    return [(split,i,[[int(v) for v in row] for row in pair['input']],
             [[int(v) for v in row] for row in (pair['output'] if 'output' in pair else gold[i])])
            for split in ('train','test') for i,pair in enumerate(task[split])]

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator, _local_imports
    # Staging may import execution-layout modules before collecting mirrored
    # task tests. Explicitly select this snapshot's own runtime, preserving the
    # source-identity guard rather than weakening it.
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        assert identity['backend']=='racket' and identity['protected'] is True
        yield apply
        bridge.close()

@pytest.mark.parametrize('split,index,grid,want',original_pairs(),ids=lambda x:None)
def test_original_python_and_protected_racket(split,index,grid,want,evaluator):
    a=load(); assert a.solve(grid)['output']==want
    assert evaluator((HOME/'reference.rkt').read_text(),grid)==want

def test_canonical_copy_and_isolated_resource_folder(tmp_path):
    import shutil
    a=load();reference=(HOME/'reference.rkt').read_bytes()
    assert a.program({'assembly_policy':'assemble'}).encode()==reference
    assert (HOME/'workspace/parametric/canonical.rkt').read_bytes()==reference
    dest=tmp_path/'isolated';shutil.copytree(HOME/'workspace/parametric',dest)
    spec=importlib.util.spec_from_file_location('cbebaa4b_relocated',dest/'adapter.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    assert mod.generate(17,{'assembly_policy':'assemble'},2,1)==a.generate(17,{'assembly_policy':'assemble'},2,1)

def test_all_count_boundaries_setting_neutrality_and_private_shuffle():
    a=load();first_sources=set()
    for seed in (0,7,17):
        full=a.generate(seed,{'assembly_policy':'assemble'},6,4)
        alt=a.generate(seed,{'assembly_policy':'deepest_piece'},6,4)
        assert [p['input'] for sp in ('train','test') for p in full[sp]]==[p['input'] for sp in ('train','test') for p in alt[sp]]
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in full[sp]})==10
        first_sources.add(full['private']['query_permutation'][0])
        for d in range(2,7):
            for q in range(1,5):
                part=a.generate(seed,{'assembly_policy':'assemble'},d,q)
                assert part['train']==full['train'][:d] and part['test']==full['test'][:q]
        for i in range(4):
            view=a.public_turn(alt,i)
            assert set(view)=={'train','test'} and view['test']==[{'input':alt['test'][i]['input']}]
    assert len(first_sources)>1

def test_two_demos_reject_executable_rivals(evaluator):
    a=load()
    for seed in (17,43):
        episode=a.generate(seed,{'assembly_policy':'deepest_piece'},2,4)
        for name,program in a.rival_programs().items():
            got=[evaluator(program,p['input']) for p in episode['train']]
            assert any(v!=p['output'] for v,p in zip(got,episode['train'])),name

def test_thirty_grid_stress_and_causal_substitution(evaluator):
    a=load();episode=a.generate(17,{'assembly_policy':'deepest_piece'},2,4)
    pairs=[p for p in episode['test'] if len(p['input'])==30 and len(p['input'][0])==30 and len(a.solve(p['input'])['pieces'])>=7]
    assert pairs
    pair=pairs[0];certificate=a.solve(pair['input'])
    assert len(certificate['pieces'])>=7
    assert certificate['depths'].count(max(certificate['depths']))==1
    assert evaluator(episode['program_solution'],pair['input'])==pair['output']
    wrong=evaluator(a.rival_programs()['euclidean'],pair['input'])
    assert wrong!=pair['output']

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True)])
def test_reject_invalid_counts(d,q):
    with pytest.raises(ValueError):load().generate(17,{'assembly_policy':'assemble'},d,q)

@pytest.mark.parametrize('settings',[{}, {'assembly_policy':True}, {'assembly_policy':'other'}, {'assembly_policy':'assemble','extra':0}])
def test_reject_invalid_settings(settings):
    with pytest.raises(ValueError):load().generate(17,settings,2,4)

def test_teaching_does_not_leak_deepest_through_smallest_piece(evaluator):
    a=load();episode=a.generate(17,{'assembly_policy':'deepest_piece'},2,4)
    smallest=a.rival_programs()['largest_original'].replace(
        '((equal? output-policy "largest_original") (pick-max moving',
        '((equal? output-policy "largest_original") (pick-min moving',1)
    got=[evaluator(smallest,p['input']) for p in episode['train']]
    assert any(y!=p['output'] for y,p in zip(got,episode['train'])), 'smallest-piece shortcut fits both demonstrations'

def test_audit_cli_writes_content_hashed_masked_views(tmp_path):
    import subprocess,sys,hashlib
    script=HOME/'workspace/parametric/audit.py'
    assert script.is_file(), 'repeatable audit CLI is missing'
    result=subprocess.run([sys.executable,str(script),'--seeds','1','--out',str(tmp_path/'audit')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr+result.stdout
    report=json.loads((tmp_path/'audit/audit.json').read_text())
    assert report['status']=='passed' and report['requests']==40 and report['public_turn_checks']==100
    for p in (tmp_path/'audit/public').glob('*.json'):
        assert hashlib.sha256(p.read_bytes()).hexdigest()==p.stem
        v=json.loads(p.read_text());assert set(v)=={'train','test'}
        assert len(v['test'])==1 and set(v['test'][0])=={'input'}


def test_direct_turn_whitelists_demonstration_fields():
    a=load();episode=a.generate(17,{'assembly_policy':'deepest_piece'},2,4)
    original=a.public_turn(episode,0)
    episode['train'][0]['private_setting']='SECRET'
    episode['train'][0]['source_seed']=17
    episode['train'][1]['future_queries']=episode['test'][1:]
    assert a.public_turn(episode,0)==original, 'direct public view leaked demo metadata'
    assert all(set(p)=={'input','output'} for p in a.public_turn(episode,0)['train'])

def test_ordinary_generator_has_no_native_folder_dependency(tmp_path):
    import shutil
    shutil.copy2(HOME/'generator.py',tmp_path/'generator.py')
    spec=importlib.util.spec_from_file_location('cbebaa_standalone',tmp_path/'generator.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    grid=m.generate(seed=17,sample_index=0,difficulty='medium')
    assert load().solve(grid)['output']==m.solve(grid)['output']
    assert m.self_check(grid,difficulty='medium')==[]

def test_second_demo_has_cycle_and_defeats_longest_simple_path():
    a=load();ep=a.generate(17,{'assembly_policy':'deepest_piece'},2,4)
    certificate=a.solve(ep['train'][1]['input'])
    edge_count=sum(map(len,certificate['graph']))//2
    assert edge_count>=len(certificate['pieces']), 'existing lessons contain trees only'
    assert a.predict(ep['train'][1]['input'],'longest_path')!=ep['train'][1]['output']
    assert any(sum(map(len,a.solve(p['input'])['graph']))//2>=len(a.solve(p['input'])['pieces']) for p in ep['test'])

def test_longest_path_counterfactual_executes_on_cycle(evaluator):
    a=load();assert 'longest_path' in a.rival_programs(), 'cycle rival missing'
    ep=a.generate(17,{'assembly_policy':'deepest_piece'},2,4)
    p=ep['train'][1]
    wrong=a.predict(p['input'],'longest_path')
    assert wrong!=p['output']
    assert evaluator(a.rival_programs()['longest_path'],p['input'])==wrong

def test_cycle_query_has_substantive_thirty_canvas():
    a=load();scene=a._bank(17)[8];g=scene[0];cert=a.solve(g)
    assert len(g)==len(g[0])==30
    assert sum(map(len,cert['graph']))//2==len(cert['pieces'])==6
    assert sum(v!=0 for row in g for v in row)>150
    assert a.predict(g,'longest_path')!=scene[2]

def test_direct_public_rejects_invalid_visible_grid():
    a=load();ep=a.generate(17,{'assembly_policy':'assemble'},2,1)
    ep['train'][0]['input'][0][0]=True
    with pytest.raises(ValueError):a.public_turn(ep,0)

@pytest.mark.parametrize('seed',[True,-1,2**63,1.0])
def test_seed_boundary(seed):
    with pytest.raises(ValueError):load().generate(seed,{'assembly_policy':'assemble'},2,4)

def test_standalone_source_matches_builder():
    p=HOME/'workspace/parametric/build_generator.py'
    spec=importlib.util.spec_from_file_location('builder_cbebaa',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert (HOME/'generator.py').read_text()==m.expected()

def load_public_io():
    path=HOME/'workspace/parametric/public_io.py';assert path.is_file(),'public verifier absent'
    spec=importlib.util.spec_from_file_location('public_io_cbebaa',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.mark.parametrize('damage',['answer','setting','future','boolean','duplicate','id','noncanonical','duplicate_key'])
def test_public_verifier_rejects_corruption(damage):
    from copy import deepcopy
    import hashlib
    io=load_public_io();a=load();view=a.public_turn(a.generate(17,{'assembly_policy':'assemble'},2,4),0)
    raw=io.encode(view);assert io.validate(raw,hashlib.sha256(raw).hexdigest())==view
    broken=deepcopy(view)
    if damage=='answer':broken['test'][0]['output']=[[8]]
    if damage=='setting':broken['settings']={'assembly_policy':'assemble'}
    if damage=='future':broken['test'].append({'input':[[1]]})
    if damage=='boolean':broken['test'][0]['input'][0][0]=True
    if damage=='duplicate':broken['test'][0]['input']=broken['train'][0]['input']
    raw=(json.dumps(broken,sort_keys=True,separators=(',',':'))+'\n').encode()
    identity=hashlib.sha256(raw).hexdigest()
    if damage=='id':identity='0'*64
    if damage=='noncanonical':raw=raw.rstrip();identity=hashlib.sha256(raw).hexdigest()
    if damage=='duplicate_key':raw=b'{"test":[],"test":[],"train":[]}\n';identity=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):io.validate(raw,identity)


def load_verifier():
    path=HOME/'workspace/parametric/verify.py';assert path.is_file(),'source-bound verifier absent'
    spec=importlib.util.spec_from_file_location('verify_cbebaa',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_verifier_rejects_stale_binding(tmp_path):
    import hashlib
    v=load_verifier();p=tmp_path/'source.py';p.write_text('a=1\n')
    receipt={'source_binding':{'files':[{'path':'source.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
    v.check_binding(tmp_path,receipt)
    p.write_text('a=2\n')
    with pytest.raises(ValueError):v.check_binding(tmp_path,receipt)

def test_difference_counts_shape_changes():
    v=load_verifier()
    assert v.difference([[1,2]],[[1,2],[3,4]])=={'overlap_changed':0,'shape_only_cells':2,'changed_cells':2,'shape_changed':True}
    assert v.difference([[1,2]],[[1,3]])['changed_cells']==1

def test_returned_metadata_cannot_mutate_cached_scene():
    from copy import deepcopy
    a=load();ep=a.generate(17,{'assembly_policy':'assemble'},2,4);expected=deepcopy(ep)
    ep['private']['scene_certificates'][0]['caller_added']='CANARY'
    assert a.generate(17,{'assembly_policy':'assemble'},2,4)==expected

@pytest.mark.parametrize('seed',range(32))
def test_stress_profiles_span_canvas(seed):
    a=load()
    for index in (8,9):
        g=a._bank(seed)[index][0];pts=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
        assert len(g)==len(g[0])==30 and len(pts)>150
        assert min(max(p[k] for p in pts)-min(p[k] for p in pts) for k in (0,1))>20
