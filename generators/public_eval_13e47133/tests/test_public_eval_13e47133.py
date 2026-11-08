import importlib.util,json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1]

def load():
    p=HOME/'workspace/parametric/prototype.py'
    assert p.exists(),'missing inward-band family'
    s=importlib.util.spec_from_file_location('rings_test_core',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_all_official_labels(split,index):
    m=load();data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['13e47133']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['13e47133']
    p=data[split][index];want=p['output'] if split=='train' else gold[index]
    assert m.solve(p['input'])==want

def test_three_color_palette_changes_bounce_at_depth_three():
    m=load()
    g=[[0]*9 for _ in range(9)]
    for r in range(9):g[r][8]=9
    g[0][0]=2;g[1][1]=3;g[2][2]=4
    cyclic=m.solve(g,'cyclic');bounce=m.solve(g,'bouncing')
    assert cyclic[3][3]==2 and bounce[3][3]==3
    assert cyclic[0][0]==bounce[0][0]==2
    assert all(cyclic[r][8]==bounce[r][8]==9 for r in range(9))

def test_racket_reference_is_authored():
    assert (HOME/'reference.rkt').exists(),'missing general Racket reference'

def adapter():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.exists(),'missing native ring adapter'
    s=importlib.util.spec_from_file_location('rings_test_adapter',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('demos',[2,3,6])
def test_matched_distinct_lessons_and_settings(demos):
    a=adapter();m=load()
    for seed in (0,17,43):
        x=a.generate(seed,{'propagation':'cyclic'},demos,4);y=a.generate(seed,{'propagation':'bouncing'},demos,4)
        assert len(x['train'])==demos and len(x['test'])==4
        assert [p['input'] for sp in ('train','test') for p in x[sp]]==[p['input'] for sp in ('train','test') for p in y[sp]]
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in x[sp]})==demos+4
        assert any(a['output']!=b['output'] for a,b in zip(x['train'],y['train']))
        assert len(x['test'][3]['input'])==len(x['test'][3]['input'][0])==30
        for p in x['train']+x['test']:assert m.solve(p['input'])==p['output']

def test_exact_canonical_and_standalone_sampler_mirror():
    a=adapter()
    assert a.program({'propagation':'cyclic'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/sampler.py').read_bytes()

@pytest.mark.parametrize('args',[(True,{'propagation':'cyclic'},2,4),(0,{},2,4),(0,{'propagation':'bad'},2,4),(0,{'propagation':'cyclic','hidden':0},2,4),(0,{'propagation':'cyclic'},1,4),(0,{'propagation':'cyclic'},7,4),(0,{'propagation':'cyclic'},2,1),(0,{'propagation':'cyclic'},2,True)])
def test_invalid_native_request_rejected(args):
    with pytest.raises((ValueError,TypeError)):adapter().generate(*args)

def test_demo_count_independent_query_bank():
    a=adapter();x=a.generate(19,{'propagation':'cyclic'},2,4);y=a.generate(19,{'propagation':'cyclic'},6,4)
    assert x['train']==y['train'][:2] and x['test']==y['test']

def test_geometry_cues_and_palettes_are_varied():
    a=adapter();m=load();counts=set();palettes=set();shapes=set()
    for seed in range(16):
        g=a.SAMPLER.generate(seed,0);bg,wall,recs=m.records(g)
        counts.add(len(recs));palettes.update(len(r['palette']) for r in recs)
        for rec in recs:
            cells=rec['cells'];r0=min(r for r,c in cells);c0=min(c for r,c in cells)
            shapes.add(tuple(sorted((r-r0,c-c0) for r,c in cells)))
    assert len(counts)>=2 and {1,2,3}<=palettes and len(shapes)>=10

def audit_module():
    p=HOME/'workspace/parametric/audit.py'
    assert p.exists(),'missing finite ring-rival audit'
    s=importlib.util.spec_from_file_location('rings_test_audit',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_two_demo_teaching_defeats_declared_harmful_rivals():
    report=audit_module().audit(range(8),(2,3,6))
    assert report['status']=='passed'
    assert report['episodes']==48 and not report['harmful_survivors']

def test_sampler_runs_without_adjacent_workspace(tmp_path):
    import subprocess,sys
    (tmp_path/'generator.py').write_bytes((HOME/'generator.py').read_bytes())
    code="import importlib.util; s=importlib.util.spec_from_file_location('relocated','generator.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); g=m.generate(17,103); assert len(g)==len(g[0])==30; print('relocated-ok')"
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,text=True,capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert 'relocated-ok' in result.stdout

@pytest.mark.parametrize('g',[[],[[False]],[[10]],[[1],[2,3]]])
def test_malformed_grids_rejected(g):
    with pytest.raises(ValueError):load().solve(g)
