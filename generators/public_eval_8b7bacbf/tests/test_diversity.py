import copy,importlib.util,json
from pathlib import Path
B=Path(__file__).resolve().parents[1]/'workspace/parametric'
s=importlib.util.spec_from_file_location('diverse8',B/'family.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)

def test_count_independent_matched_streams():
 for seed in (0,17,43):
  e=F.generate(seed,{'indicator_policy':'clean'},6,4)
  for demos in range(2,7):
   for queries in (1,4):
    for mode in F.MODES:
     x=F.generate(seed,{'indicator_policy':mode},demos,queries)
     assert [p['input']for p in x['train']]==[p['input']for p in e['train'][:demos]]
     assert [p['input']for p in x['test']]==[p['input']for p in e['test'][:queries]]

def test_selected_pockets_change_with_route_only():
 for seed in (0,17,43):
  a=F.scene(seed,0);b=F.scene(seed,0,route_offset=1);da=F.analyze(a);db=F.analyze(b)
  assert sorted(sorted(c)for c,s in da['pockets'])==sorted(sorted(c)for c,s in db['pockets'])
  assert {tuple(sorted(c))for c,s in da['pockets']if s}!={tuple(sorted(c))for c,s in db['pockets']if s}

def test_dense_large_inputs_have_substantive_structure():
 for seed in (0,17,43):
  g=F.scene(seed,0);d=F.analyze(g)
  assert len(g)==len(g[0])==30 and len(d['pockets'])==16
  assert sum(v!=d['background']for row in g for v in row)>=250
  assert 1<sum(s for c,s in d['pockets'])<len(d['pockets'])

def test_strict_requests_and_visibility():
 setting={'indicator_policy':'clean'}
 for args in [(True,setting,2,4),(0,setting,True,4),(0,setting,2,True),(0,setting,1,4),(0,setting,2,5),(0,{},2,4),(0,{'indicator_policy':True},2,4)]:
  try:F.generate(*args)
  except ValueError:pass
  else:raise AssertionError(args)
 e=F.generate(17,setting,2,4);before=F.public_view(e,0);e['test'][0]['output']=[[999]];e['test'][1:]=[];e['program_solution']='secret';assert before==F.public_view(e,0)
