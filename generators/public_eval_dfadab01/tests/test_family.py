from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p/'shared/runtime').is_dir())

def load(name='adapter'):
    path=HOME/'workspace/parametric'/f'{name}.py'
    assert path.is_file(), f'missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location('dfad_test_'+name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def originals():
    p=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['dfadab01']
    s=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['dfadab01']
    return p['train']+[{'input':x['input'],'output':y} for x,y in zip(p['test'],s)]

@pytest.mark.parametrize('pair', originals())
def test_original_python(pair):
    assert load('prototype').solve([[int(c) for c in r] for r in pair['input']])==[[int(c) for c in r] for r in pair['output']]

def test_exact_canonical():
    a=load(); assert a.program({'finish_rule':'decode'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,17,43,101])
def test_counts_prefix_matching(seed):
    a=load(); full=a.generate(seed,{'finish_rule':'decode'},6,4)
    for d in range(2,7):
        for q in range(1,5):
            e=a.generate(seed,{'finish_rule':'decode'},d,q)
            f=a.generate(seed,{'finish_rule':'highlight_largest'},d,q)
            assert e['train']==full['train'][:d] and e['test']==full['test'][:q]
            assert [p['input'] for s in ('train','test') for p in e[s]]==[p['input'] for s in ('train','test') for p in f[s]]
            xs=[json.dumps(p['input']) for s in ('train','test') for p in e[s]]
            assert len(set(xs))==len(xs)
            assert all(e['train'][i]['output']!=f['train'][i]['output'] for i in range(d))
    g=full['test'][3]['input']; assert len(g)==len(g[0])==30
    assert sum(v!=0 for row in g for v in row)>=20
    out=full['test'][3]['output']
    assert all(any(out[r][c] for r,c in edge) for edge in (
        [(0,c) for c in range(30)],[(29,c) for c in range(30)],[(r,0) for r in range(30)],[(r,29) for r in range(30)]))

@pytest.mark.parametrize('settings',[{}, {'finish_rule':'bogus'}, {'finish_rule':True}, {'finish_rule':'decode','other':0},None])
def test_bad_settings(settings):
    with pytest.raises((TypeError,ValueError)): load().program(settings)

@pytest.mark.parametrize('seed,d,q',[(True,2,4),(-1,2,4),(1,1,4),(1,7,4),(1,2,0),(1,2,5),(1,2,True),(1,2.0,4)])
def test_bad_counts(seed,d,q):
    with pytest.raises((TypeError,ValueError)): load().generate(seed,{'finish_rule':'decode'},d,q)

def test_legend_and_marker_in_blank_corner():
    p=load('prototype');g=[[0]*10 for _ in range(10)]
    for r in range(4):
        for c in range(4):g[r+1][c+1]=p.symbol(3,r,c)
    g[5][5]=3 # legend code: must disappear
    g[1][1]=3 # valid anchor in circle's blank corner: must be drawn
    y=p.solve(g)
    assert y[1:5]==[[0]+[p.symbol(3,r,c) for c in range(4)]+[0]*5 for r in range(4)]
    assert all(v==0 for row in y[5:] for v in row)


def test_literal_component_highlight():
    p=load('prototype');g=[[0]*14 for _ in range(10)]
    g[0][0]=2;g[0][4]=2;g[6][10]=3
    y=p.solve(g,'highlight_largest')
    assert sum(v==9 for row in y for v in row)==24
    assert sum(v==1 for row in y for v in row)==8

def test_presentation_single_turn_and_private_invariance():
    a=load();p=load('presentation');e=a.generate(17,{'finish_rule':'decode'},2,4);e['seed']=17
    full=p.prepare(e,5,limit=4);one=p.prepare(e,5,limit=1)
    assert one['views']==full['views'][:1]
    assert len({v['id'] for v in full['views']})==4
    for row in full['views']:
        assert set(row)=={'id','challenge'}
        assert set(row['challenge'])=={'train','test'}
        assert len(row['challenge']['test'])==1 and set(row['challenge']['test'][0])=={'input'}
    changed=json.loads(json.dumps(e));changed['settings']={'secret':'different'};changed['program_solution']='private-change'
    assert p.prepare(changed,5,limit=4)['views']==full['views']
    assert len({tuple(p.prepare(e,s)['source_indices']) for s in range(10)})>1
    assert any(p.prepare(e,s)['source_indices'][0]!=0 for s in range(10))
    with pytest.raises(ValueError):p.prepare(a.generate(17,{'finish_rule':'decode'},2,1),5)


def test_rivals_are_executable_candidates():
    r=load('rivals');a=load()
    for mode in a.P.SETTINGS:
        pool=r.programs(mode)
        assert len(pool)>=4 and len(set(pool.values()))==len(pool)
        assert all(text.startswith('(rule!') for text in pool.values())
        assert a.program({'finish_rule':mode}) not in pool.values()

def test_production_generator_survives_relocation(tmp_path):
    import shutil
    copy=tmp_path/'public_eval_dfadab01'
    shutil.copytree(HOME,copy,ignore=shutil.ignore_patterns('__pycache__','tests','evidence'))
    spec=importlib.util.spec_from_file_location('relocated_dfad_generator',copy/'generator.py')
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    assert Path(gen.P.__file__).is_relative_to(copy)
    first=gen.generate(29,0);assert first==gen.generate(29,0) and gen.self_check(first)==[]
    assert gen.generate(29,1)!=first
    with pytest.raises(ValueError):gen.generate(29,0,unknown=1)
    assert gen.GENERATOR_ID=='public_eval_dfadab01'


def test_public_writer_hashes_the_exact_canonical_saved_bytes(tmp_path):
    import hashlib
    from reviewer_support import public_challenge_bytes
    a=load();p=load('presentation');e=a.generate(17,{'finish_rule':'decode'},2,4)
    bank=p.prepare(e,13)
    for v in bank['views']:
        assert v['id']==hashlib.sha256(public_challenge_bytes(v['challenge'])).hexdigest()
    paths=p.write_views(bank,tmp_path/'public')
    assert len(paths)==4
    for path,v in zip(paths,bank['views']):
        assert path.read_bytes()==public_challenge_bytes(v['challenge'])
        assert path.stem==hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):p.write_views(bank,tmp_path/'public')
    bad={'views':[bank['views'][0],bank['views'][0]]}
    with pytest.raises(ValueError):p.write_views(bad,tmp_path/'duplicates')
