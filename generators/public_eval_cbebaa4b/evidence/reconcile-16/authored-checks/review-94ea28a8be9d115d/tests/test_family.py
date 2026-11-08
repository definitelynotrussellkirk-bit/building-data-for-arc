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

def original_pairs():
    task=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['cbebaa4b']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['cbebaa4b']
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
    pairs=[p for p in episode['test'] if len(p['input'])==30 and len(p['input'][0])==30]
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
