import hashlib,json,pathlib,sys
from reviewer_support import find_root,load_selected_generator
ROOT=find_root(__file__);OUT=pathlib.Path(__file__).parent;TASK='483d78b1d04b'
m,source,sha=load_selected_generator(TASK,root=ROOT)
def geometry(g):
 cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==5]
 return min(r for r,c in cells),max(r for r,c in cells),min(c for r,c in cells),max(c for r,c in cells)
def border(g):
 out=[row[:] for row in g];a,b,c,d=geometry(g);color=next(v for row in g for v in row if v not in(0,5))
 for r in range(a+1,b):
  for col in range(c+1,d):
   if r in(a+1,b-1) or col in(c+1,d-1):out[r][col]=color
 return out
def filled(g):
 out=[row[:] for row in g];a,b,c,d=geometry(g);color=next(v for row in g for v in row if v not in(0,5))
 for r in range(a+1,b):
  for col in range(c+1,d):out[r][col]=color
 return out
found=None
for seed in range(1000):
 pairs=[];seen=set()
 for index in range(32):
  g=m.generate(seed,index,difficulty='easy');k=tuple(map(tuple,g))
  if m.self_check(g) or k in seen:continue
  seen.add(k);pairs.append({'sample_index':index,'input':g,'border_prediction':border(g),'filled_rival_prediction':filled(g)})
  if len(pairs)==4:break
 if len(pairs)==4 and all(p['border_prediction']==p['filled_rival_prediction'] for p in pairs[:3]) and pairs[3]['border_prediction']!=pairs[3]['filled_rival_prediction']:
  found={'seed':seed,'difficulty':'easy','assembly':'First four distinct self_check-accepted inputs at increasing sample_index0..31; direct generator authoring probe, not production export.','pairs':pairs};break
bad=[[0]*6 for _ in range(6)]
for col in range(1,5):bad[2][col]=5
bad[3][3]=2
same=[]
for flag in ('anchor_inset','asymmetry_force','marker_offset_kind'):
 values=('tight','loose') if flag=='marker_offset_kind' else(False,True)
 same.append({'override':flag,'values':values,'equal_for_30_seeds':all(m.generate(s,0,**{flag:values[0]})==m.generate(s,0,**{flag:values[1]}) for s in range(30))})
report={'task_id':TASK,'generator_sha256':sha,'validator_counterexample':{'input':bad,'self_check':m.self_check(bad),'documented_precondition':'Four gray rectangle corners; this input instead has all four gray markers in one row.'},'inert_override_probes':same,'filled_rectangle_lesson_probe':found,'probe_scope':{'seeds_examined':seed+1,'seed_range':[0,seed]},'invocation':{'cwd':str(pathlib.Path.cwd()),'argv':[sys.executable,*sys.argv]}}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
inputs=[bad]+([p['input'] for p in found['pairs']] if found else[])
(OUT/'input.json').write_text(json.dumps(inputs)+'\n')
print(json.dumps({'generator_sha256':sha,'validator_errors':m.self_check(bad),'inert_override_probes':same,'lesson_seed':None if found is None else found['seed'],'seeds_examined':seed+1}))
