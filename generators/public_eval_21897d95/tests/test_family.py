from pathlib import Path
import importlib.util,json,copy
import pytest
HOME=Path(__file__).resolve().parents[1]
def load(name='generator',sidecar=False):
 p=(HOME/'workspace/parametric' if sidecar else HOME)/(name+'.py')
 assert p.exists(), 'missing implementation: '+str(p)
 s=importlib.util.spec_from_file_location('_region_arrows_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_all_original_labels():
 m=load()
 for p in json.loads((HOME/'tests/originals.json').read_text()):
  assert m.solve(p['input'])==p['output'],(p['split'],p['index'])

def test_literal_arrow_targets_other_region_without_recolor_cascade():
 m=load();g=[[2]*5+[3]*5 for _ in range(5)]
 # Right-pointing T: blue north/south/east, payload 4 at center.
 for r,c,v in [(1,2,1),(2,2,4),(3,2,1),(2,3,1)]:g[r][c]=v
 want=[[2]*5+[4]*5 for _ in range(5)]
 assert m.solve(g)==want
 assert m.solve(g,'source_color')==[[2]*10 for _ in range(5)]

def test_program_and_engine_bytes():
 a=load('adapter',True)
 assert a.program({'ink':'payload'})==(HOME/'reference.rkt').read_text()
 assert a.program({'ink':'source_color'})!=a.program({'ink':'payload'})
 assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/engine.py').read_bytes()

def test_prefix_matched_inputs_and_dense_stress():
 a=load('adapter',True);m=load()
 for seed in (0,1,17,2**63-1):
  banks=[a.generate(seed,{'ink':mode},6,4) for mode in m.SETTINGS]
  for mode,bank in zip(m.SETTINGS,banks):
   for d,q in ((2,1),(3,2),(6,4)):
    ep=a.generate(seed,{'ink':mode},d,q)
    assert ep['train']==bank['train'][:d] and ep['test']==bank['test'][:q]
   assert len({json.dumps(p['input']) for sp in ('train','test') for p in bank[sp]})==10
   assert all(not m.self_check(p['input']) for sp in ('train','test') for p in bank[sp])
  assert [p['input'] for sp in ('train','test') for p in banks[0][sp]]==[p['input'] for sp in ('train','test') for p in banks[1][sp]]
  assert any(p['output']!=q['output'] for p,q in zip(banks[0]['train'][:2],banks[1]['train'][:2]))
  g=banks[0]['test'][3]['input'];assert len(g)==len(g[0])==30
  info=m.analyze(g);assert len(info['arrows'])>=4 and len(info['regions'])>=5

@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('seed',1.0),('seed',2**63),('demos',True),('demos',1),('demos',7),('queries',0),('queries',5),('queries',2.0)])
def test_bad_controls(field,value):
 kw={'seed':0,'settings':{'ink':'payload'},'demos':2,'queries':4};kw[field]=value
 with pytest.raises(ValueError):load('adapter',True).generate(**kw)
@pytest.mark.parametrize('settings',[None,{}, {'ink':'bad'},{'ink':True},{'ink':'payload','extra':0}])
def test_bad_settings(settings):
 with pytest.raises(ValueError):load('adapter',True).program(settings)
@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1.0]],[[10]],[[0],[0,1]]])
def test_bad_grid(g):
 with pytest.raises(ValueError):load().solve(g)

def test_rivals_are_total_and_rejected():
 a=load('adapter',True);m=load();au=load('audit_lessons',True)
 for seed in range(4):
  for mode in m.SETTINGS:
   ep=a.generate(seed,{'ink':mode},2,4)
   for name in au.RIVALS:
    labels=[au.rival(p['input'],mode,name) for p in ep['train']+ep['test']]
    for label in labels:m.grid_check(label)
    assert any(labels[i]!=p['output'] for i,p in enumerate(ep['train'])),(seed,mode,name)

def test_rotation_symbol_does_not_corrupt_arrow_context():
 m=load()
 for seed,index in ((0,0),(10,3),(23,3)):
  g=m.scene(seed,index,'demo')
  assert m.self_check(g)==[]
  assert len(m.analyze(g)['arrows'])==6
