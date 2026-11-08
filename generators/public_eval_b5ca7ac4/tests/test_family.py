from pathlib import Path
import importlib.util
import json,sys
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/runtime').is_dir())

def load(name='adapter'):
    path=HOME/'workspace/parametric'/f'{name}.py'
    assert path.is_file(),f'missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location('b5_test_'+name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def originals():
    p=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['b5ca7ac4']
    s=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['b5ca7ac4']
    return p['train']+[{'input':x['input'],'output':y} for x,y in zip(p['test'],s)]

@pytest.mark.parametrize('pair', originals())
def test_original_python(pair):
    assert load('prototype').solve([[int(c) for c in r] for r in pair['input']])==[[int(c) for c in r] for r in pair['output']]

def box(g,r,c,h,w,b,inside):
    for i in range(h):
        for j in range(w):g[r+i][c+j]=b if i in (0,h-1) or j in (0,w-1) else inside

def test_literal_settled_not_original_positions():
    p=load('prototype');g=[[0]*20 for _ in range(8)]
    box(g,0,12,5,5,8,1);box(g,3,2,5,5,8,3)
    expected=[[0]*20 for _ in range(8)];box(expected,0,5,5,5,8,1);box(expected,3,0,5,5,8,3)
    assert p.solve(g)==expected
    top=[[0]*20 for _ in range(8)];box(top,0,0,5,5,8,1);box(top,3,5,5,5,8,3)
    assert p.solve(g,'top_first')==top

def test_adjacent_frames_and_other_border_interior():
    p=load('prototype');g=[[4]*16 for _ in range(7)]
    box(g,0,1,4,4,8,2);box(g,2,5,4,5,8,1)
    found=p.extract(g)
    assert [(b.r,b.c,b.h,b.w,b.border,b.fill) for b in found]==[(0,1,4,4,8,2),(2,5,4,5,8,1)]

def test_exact_canonical():
    a=load();assert a.program({'packing_order':'front_first'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,17,43,101])
def test_counts_prefix_matching(seed):
    a=load();base=a.generate(seed,{'packing_order':'front_first'},6,4)
    for d in range(2,7):
        for q in range(1,5):
            e=a.generate(seed,{'packing_order':'front_first'},d,q);f=a.generate(seed,{'packing_order':'top_first'},d,q)
            assert e['train']==base['train'][:d] and e['test']==base['test'][:q]
            assert [x['input'] for s in ('train','test') for x in e[s]]==[x['input'] for s in ('train','test') for x in f[s]]
            xs=[json.dumps(x['input']) for s in ('train','test') for x in e[s]];assert len(set(xs))==len(xs)
            assert any(x['output']!=y['output'] for x,y in zip(e['train'],f['train']))
    g=base['test'][3]['input'];assert len(g)==len(g[0])==30
    bg=a.P.background(g)
    assert sum(v!=bg for row in g for v in row)>=120
    assert all(any(g[r][c]!=bg for r,c in edge) for edge in (
        [(0,c) for c in range(30)],[(29,c) for c in range(30)],[(r,0) for r in range(30)],[(r,29) for r in range(30)]))

@pytest.mark.parametrize('settings',[{}, {'packing_order':'bogus'}, {'packing_order':True}, {'packing_order':'front_first','other':0},None])
def test_bad_settings(settings):
    with pytest.raises((TypeError,ValueError)):load().program(settings)

@pytest.mark.parametrize('seed,d,q',[(True,2,4),(-1,2,4),(1,1,4),(1,7,4),(1,2,0),(1,2,5),(1,2,True),(1,2.0,4)])
def test_bad_counts(seed,d,q):
    with pytest.raises((TypeError,ValueError)):load().generate(seed,{'packing_order':'front_first'},d,q)


def test_presentation_single_turn_and_private_invariance():
    a=load();p=load('presentation');e=a.generate(17,{'packing_order':'front_first'},2,4);e['seed']=17
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
    with pytest.raises(ValueError):p.prepare(a.generate(17,{'packing_order':'front_first'},2,1),5)


def test_rivals_are_executable_candidates():
    r=load('rivals');a=load()
    for mode in a.P.SETTINGS:
        pool=r.programs(mode)
        assert len(pool)>=4 and len(set(pool.values()))==len(pool)
        assert all(text.startswith('(rule!') for text in pool.values())
        assert a.program({'packing_order':mode}) not in pool.values()

def test_production_generator_survives_relocation(tmp_path):
    import shutil
    copy=tmp_path/'public_eval_b5ca7ac4'
    shutil.copytree(HOME,copy,ignore=shutil.ignore_patterns('__pycache__','tests','evidence'))
    spec=importlib.util.spec_from_file_location('relocated_b5_generator',copy/'generator.py')
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    assert Path(gen.P.__file__).is_relative_to(copy)
    first=gen.generate(29,0);assert first==gen.generate(29,0) and gen.self_check(first)==[]
    assert gen.generate(29,1)!=first
    with pytest.raises(ValueError):gen.generate(29,0,unknown=1)
    assert gen.GENERATOR_ID=='public_eval_b5ca7ac4'

def test_enclosed_background_gap_is_not_an_extra_payload():
    p=load('prototype');g=[[6]*14 for _ in range(12)]
    box(g,0,5,5,4,2,8);box(g,2,9,5,3,2,3)
    box(g,4,0,5,5,2,3);box(g,6,5,5,4,2,3)
    assert [(b.r,b.c,b.h,b.w) for b in p.extract(g)]==[(0,5,5,4),(2,9,5,3),(4,0,5,5),(6,5,5,4)]


def test_public_writer_hashes_the_exact_canonical_saved_bytes(tmp_path):
    import hashlib
    from reviewer_support import public_challenge_bytes
    a=load();p=load('presentation');e=a.generate(17,{'packing_order':'front_first'},2,4)
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
