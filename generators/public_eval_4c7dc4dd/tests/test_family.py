from pathlib import Path
import importlib.util,json,copy
import pytest
HOME=Path(__file__).resolve().parents[1]
def load(name='generator',sidecar=False):
 p=(HOME/'workspace/parametric' if sidecar else HOME)/(name+'.py')
 assert p.exists(), 'missing implementation: '+str(p)
 s=importlib.util.spec_from_file_location('_analogy_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_originals():
 m=load()
 for p in json.loads((HOME/'tests/originals.json').read_text()):
  assert m.solve(p['input'])==p['output'],(p['split'],p['index'])

def test_line_chain_preserves_bends_and_connects_endpoints():
 m=load();g=[[2,0,0,0],[6,0,0,6],[0,0,0,0],[0,0,0,2]]
 assert m.line_complete(g)==[[2,0,0,0],[6,2,2,6],[0,0,0,2],[0,0,0,2]]

def test_symmetry_requires_measured_nonzero_orbits():
 m=load();g=[[0,8,0,0],[8,3,0,0],[0,0,0,0],[0,0,0,0]]
 assert m.reflect_complete(g)==[[0,8,8,0],[8,3,3,8],[8,3,3,8],[0,8,8,0]]

def test_complement_transfers_measured_texture_palette():
 m=load();texture=[[8,1,8],[1,8,1],[8,1,8]];g=[[0,4,0],[4,2,4],[0,4,0]]
 assert m.complement(g,texture)==[[2,0,2],[0,0,0],[2,0,2]]

def test_program_and_standalone_copy():
 a=load('adapter',True)
 assert a.program({'view':'complete'})==(HOME/'reference.rkt').read_text()
 assert a.program({'view':'changes_only'})!=a.program({'view':'complete'})
 assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/engine.py').read_bytes()

def test_prefix_matched_settings_and_four_distinct_queries():
 a=load('adapter',True);m=load()
 for seed in (0,1,17,2**63-1):
  banks=[a.generate(seed,{'view':mode},6,4) for mode in m.SETTINGS]
  for mode,bank in zip(m.SETTINGS,banks):
   for d,q in ((2,1),(3,2),(6,4)):
    ep=a.generate(seed,{'view':mode},d,q)
    assert ep['train']==bank['train'][:d] and ep['test']==bank['test'][:q]
   assert len({json.dumps(p['input']) for sp in ('train','test') for p in bank[sp]})==10
   assert all(not m.self_check(p['input']) for sp in ('train','test') for p in bank[sp])
  assert [p['input'] for sp in ('train','test') for p in banks[0][sp]]==[p['input'] for sp in ('train','test') for p in banks[1][sp]]
  assert any(p['output']!=q['output'] for p,q in zip(banks[0]['train'][:2],banks[1]['train'][:2]))
  g=banks[0]['test'][3]['input'];assert len(g)==len(g[0])==30
  assert len(m.analyze(g)['frames'])==4 and len(m.solve(g))>=6

@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('seed',1.0),('seed',2**63),('demos',True),('demos',1),('demos',7),('queries',0),('queries',5),('queries',2.0)])
def test_bad_controls(field,value):
 kw={'seed':0,'settings':{'view':'complete'},'demos':2,'queries':4};kw[field]=value
 with pytest.raises(ValueError):load('adapter',True).generate(**kw)
@pytest.mark.parametrize('settings',[None,{}, {'view':'bad'},{'view':True},{'view':'complete','extra':0}])
def test_bad_settings(settings):
 with pytest.raises(ValueError):load('adapter',True).program(settings)
@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1.0]],[[10]],[[0],[0,1]]])
def test_bad_grid(g):
 with pytest.raises(ValueError):load().solve(g)

def test_total_rivals_cannot_fit_both_demos():
 a=load('adapter',True);m=load();au=load('audit_lessons',True)
 for seed in range(4):
  for mode in m.SETTINGS:
   ep=a.generate(seed,{'view':mode},2,4)
   for name in au.RIVALS:
    labels=[au.rival(p['input'],mode,name) for p in ep['train']+ep['test']]
    for label in labels:m.grid_check(label)
    assert any(labels[i]!=p['output'] for i,p in enumerate(ep['train'])),(seed,mode,name)

def test_transfer_uses_reference_completion_not_only_mirrored_seed():
 m=load();small=[[0]*6 for _ in range(6)];small[0][1]=small[1][0]=8;small[1][1]=3
 full=[[3]*6 for _ in range(6)]
 for r,c,v in [(0,0,0),(0,1,8),(1,0,8)]:
  for rr in (r,5-r):
   for cc in (c,5-c):full[rr][cc]=v
 q=[[6 if v==3 else v for v in row[::-1]] for row in small]
 expected=[[6 if v==3 else v for v in row] for row in full]
 assert m.infer(small,full,q)[1]==expected
