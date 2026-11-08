from pathlib import Path
import runpy
M=runpy.run_path(str(Path(__file__).resolve().parents[1]/'workspace/parametric/union_family.py'))
def test_matched_inputs_and_no_named_or_fixed_size_shortcuts():
 for seed in range(30):
  inputs=None
  for v in M['VALUES']:
   e=M['generate'](seed,{'vector_direction':v},2,4)
   assert not M['findings'](e,v),(seed,v,M['findings'](e,v))
   actual=[p['input'] for p in e['train']+e['test']]
   if inputs is not None:assert actual==inputs
   inputs=actual
   large=M['generate'](seed,{'vector_direction':v},6,4)
   assert large['train'][:2]==e['train'] and large['test']==e['test']
   sizes=[max(map(len,M['incoming']._visible_components(g))) for g in inputs]
   assert len(set(sizes[:2]))==2 and len(set(sizes[2:]))>=3
   assert any(len(g)==len(g[0])==30 for g in inputs)
   if v=='largest_visible_fragment':
    for fixed in set(sizes):
     preds=[]
     for g in inputs[:2]:
      out=M['incoming'].canonical_intermediate(g)
      for part in M['incoming']._visible_components(g):
       if len(part)==fixed:
        for r,c in part:out[r][c]=4
      preds.append(out)
     assert any(a!=p['output'] for a,p in zip(preds,e['train']))

def _axis_projection(g,v,keep):
 info=M['old'].analyze(g,'red_to_blue' if v=='red_to_blue' else 'blue_to_red')
 dr,dc=info['applied_vector']
 if keep=='vertical':dc=0
 else:dr=0
 out=[[0]*len(g[0]) for _ in g]
 for r,c in info['source_cells']:
  if 0<=r+dr<len(g) and 0<=c+dc<len(g[0]):out[r+dr][c+dc]=8
 if v=='largest_visible_fragment':
  parts=M['incoming']._components_from_cells(M['incoming']._positions(out,8))
  if parts:
   chosen=sorted(parts,key=lambda s:(-len(s),min(s)))[0]
   for r,c in chosen:out[r][c]=4
 return out

def test_both_vector_components_are_taught_at_minimum_demos():
 for seed in range(30):
  for v in M['VALUES']:
   e=M['generate'](seed,{'vector_direction':v},2,4)
   vectors=[M['old'].analyze(p['input'],'blue_to_red')['base_vector'] for p in e['train']]
   assert all(dr and dc for dr,dc in vectors), (seed,v,vectors)
   for keep in ('vertical','horizontal'):
    assert all(_axis_projection(p['input'],v,keep)!=p['output'] for p in e['train']), (seed,v,keep)
   qvec=[M['old'].analyze(p['input'],'blue_to_red')['base_vector'] for p in e['test']]
   assert any(dr and dc for dr,dc in qvec)
   assert any(not dr or not dc for dr,dc in qvec)
