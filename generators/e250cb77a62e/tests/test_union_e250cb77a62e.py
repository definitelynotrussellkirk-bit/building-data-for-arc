from pathlib import Path
import runpy,hashlib
M=runpy.run_path(str(Path(__file__).resolve().parents[1]/'workspace/parametric/union_family.py'))
def test_exact_programs_and_minimal_teaching():
 for seed in range(12):
  inputs=None
  for v in M['VALUES']:
   e=M['generate'](seed,{'stamp_policy':v},2,4)
   assert not M['findings'](e,v)
   actual=[p['input'] for p in e['train']+e['test']]
   if inputs is not None:assert actual==inputs
   inputs=actual
   large=M['generate'](seed,{'stamp_policy':v},6,4)
   assert large['train'][:2]==e['train'] and large['test']==e['test']
   sizes=[len(M['old'].intermediate(g)['largest_cells']) for g in inputs]
   assert len(set(sizes[:2]))==2 and len(set(sizes[2:]))>=3
   assert any(len(g)==len(g[0])==30 for g in inputs)
   for fixed in set(sizes):
    # A fixed component-size selector must be refuted in the demonstrations.
    preds=[]
    for g in inputs[:2]:
     out=M['old'].predict(g,'all_stamps');parts=M['old'].components(M['old'].scene(g)['stamped'])
     for s in parts:
      if len(s)==fixed:
       for r,c in s:out[r][c]=3
     preds.append(out)
    if v=='largest_joined':assert any(a!=p['output'] for a,p in zip(preds,e['train']))
