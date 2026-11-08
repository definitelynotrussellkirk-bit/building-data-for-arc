from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter is missing'
    spec=importlib.util.spec_from_file_location('6e453dd6_test_adapter',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def original_pairs():
    task=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['6e453dd6']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['6e453dd6']
    return [(split,i,[[int(v) for v in row] for row in pair['input']],
             [[int(v) for v in row] for row in (pair['output'] if 'output' in pair else gold[i])])
            for split in ('train','test') for i,pair in enumerate(task[split])]

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()

@pytest.mark.parametrize('split,index,grid,want',original_pairs())
def test_original_python_and_protected_racket(split,index,grid,want,evaluator):
    a=load();assert a.predict(grid,'all_exposed')==want
    assert evaluator((HOME/'reference.rkt').read_text(),grid)==want

@pytest.mark.parametrize('pose',range(8))
def test_full_dihedral_equivariance(pose,evaluator):
    a=load();_,_,grid,want=original_pairs()[0]
    assert evaluator(a.program({'signal_policy':'all_exposed'}),a.d4(grid,pose))==a.d4(want,pose)

def test_canonical_copy_and_resource_only_relocation(tmp_path):
    import shutil
    a=load();assert a.program({'signal_policy':'all_exposed'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (HOME/'workspace/parametric/canonical.rkt').read_bytes()==(HOME/'reference.rkt').read_bytes()
    shutil.copytree(HOME/'workspace/parametric',tmp_path/'native')
    spec=importlib.util.spec_from_file_location('relocated_6e453dd6',tmp_path/'native/adapter.py')
    other=importlib.util.module_from_spec(spec);spec.loader.exec_module(other)
    assert other.generate(43,{'signal_policy':'largest_exposed'},2,1)==a.generate(43,{'signal_policy':'largest_exposed'},2,1)

def test_counts_prefix_privacy_and_setting_neutrality():
    a=load();first_sources=set()
    for seed in (0,7,17):
        full=a.generate(seed,{'signal_policy':'all_exposed'},6,4)
        alt=a.generate(seed,{'signal_policy':'largest_exposed'},6,4)
        first_sources.add(full['private']['query_permutation'][0])
        assert [p['input'] for sp in ('train','test') for p in full[sp]]==[p['input'] for sp in ('train','test') for p in alt[sp]]
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in full[sp]})==10
        for d in range(2,7):
            for q in range(1,5):
                part=a.generate(seed,{'signal_policy':'all_exposed'},d,q)
                assert part['train']==full['train'][:d] and part['test']==full['test'][:q]
        for i in range(4):
            view=a.public_turn(alt,i);assert set(view)=={'train','test'}
            assert view['test']==[{'input':alt['test'][i]['input']}]
    assert len(first_sources)>1

def test_two_demonstrations_reject_all_declared_wrong_rules(evaluator):
    a=load()
    for seed in (17,43):
        ep=a.generate(seed,{'signal_policy':'largest_exposed'},2,4)
        for name,program in a.rival_programs().items():
            labels=[evaluator(program,p['input']) for p in ep['train']]
            assert any(y!=p['output'] for y,p in zip(labels,ep['train'])),name

def test_thirty_canvas_has_buried_and_open_distractors(evaluator):
    a=load();ep=a.generate(17,{'signal_policy':'largest_exposed'},2,4)
    pair=next(p for p in ep['test'] if len(p['input'])==30 and len(p['input'][0])==30)
    cert=a.analyze(pair['input']);exposed=cert['exposed']
    assert len(cert['objects'])>=5 and len(exposed)>=3
    assert max(len(h['cells']) for h in cert['holes'])>max(len(h['cells']) for h in exposed)
    assert len({len(h['cells']) for h in exposed})==len(exposed)
    assert evaluator(ep['program_solution'],pair['input'])==pair['output']
    assert evaluator(a.rival_programs()['largest_bbox'],pair['input'])!=pair['output']

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True)])
def test_reject_invalid_counts(d,q):
    with pytest.raises(ValueError):load().generate(17,{'signal_policy':'all_exposed'},d,q)

@pytest.mark.parametrize('settings',[{}, {'signal_policy':True}, {'signal_policy':'other'}, {'signal_policy':'all_exposed','extra':0}])
def test_reject_invalid_settings(settings):
    with pytest.raises(ValueError):load().generate(17,settings,2,4)

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
    a=load();episode=a.generate(17,{'signal_policy':'largest_exposed'},2,4)
    original=a.public_turn(episode,0)
    episode['train'][0]['private_setting']='SECRET'
    episode['train'][0]['source_seed']=17
    episode['train'][1]['future_queries']=episode['test'][1:]
    assert a.public_turn(episode,0)==original, 'direct public view leaked demo metadata'
    assert all(set(p)=={'input','output'} for p in a.public_turn(episode,0)['train'])
