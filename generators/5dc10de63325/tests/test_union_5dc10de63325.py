from pathlib import Path
import runpy
M=runpy.run_path(str(Path(__file__).resolve().parents[1]/'workspace/parametric/union_family.py'))
def test_all_rivals_and_selector_diversity():
 colors=set();largest=set()
 for seed in range(12):
  inputs=None
  for v in M['VALUES']:
   e=M['generate'](seed,{'fill_order':v},4,4)
   assert not M['findings'](e,v),(seed,v,M['findings'](e,v))
   actual=[p['input'] for p in e['train']+e['test']]
   if inputs is not None:assert actual==inputs
   inputs=actual
   full=M['generate'](seed,{'fill_order':v},6,4)
   assert full['train'][:4]==e['train'] and full['test']==e['test']
  selected=[M['incoming'].explain_dependency(g)['selected_color'] for g in inputs]
  assert len(set(selected[:4]))==4 and len(set(selected[4:]))==4
  colors.update(selected)
  sizes=[max(M['old'].cyan_sizes(g)) for g in inputs];largest.update(sizes)
  assert len(set(sizes[:4]))>=3 and len(set(sizes[4:]))>=3
  # Constant center color and constant largest-count output are refuted by demos.
  relay=M['generate'](seed,{'fill_order':'bucket_color_relay'},4,4)
  for color in range(1,10):assert any(p['output'][2][2]!=color for p in relay['train'])
  component=M['generate'](seed,{'fill_order':'largest_component_count'},4,4)
  assert len({str(p['output']) for p in component['train']})>=3
  stress=next(g for g in inputs if len(g)==len(g[0])==30)
  cells=[(r,c) for r,row in enumerate(stress) for c,v in enumerate(row) if v]
  assert max(r for r,c in cells)-min(r for r,c in cells)==29
  assert max(c for r,c in cells)-min(c for r,c in cells)==29
 assert colors==set(range(1,8)) and len(largest)>=8
