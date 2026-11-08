from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
from collections import Counter, deque

ROOT=Path('/mnt/data/arc_review_round5/WORK/repo')
sys.path[:0]=[str(ROOT/'shared/runtime'),str(ROOT/'src')]
from reviewer_support import canonical_pairs, find_root


def load(task):
 p=ROOT/f'generators/{task}/generator.py'
 spec=importlib.util.spec_from_file_location(f'audit_{task}',p)
 m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
 return m,p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def components7(g):
 h,w=len(g),len(g[0]); seen=set(); n=0
 for r in range(h):
  for c in range(w):
   if g[r][c]!=7 or (r,c) in seen: continue
   n+=1; q=deque([(r,c)]);seen.add((r,c))
   while q:
    rr,cc=q.popleft()
    for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
     p=(rr+dr,cc+dc)
     if 0<=p[0]<h and 0<=p[1]<w and p not in seen and g[p[0]][p[1]]==7:
      seen.add(p);q.append(p)
 return n

# 49a
T='49a0b77dcc7f'; m,p=load(T); pairs=canonical_pairs(T,root=ROOT)
rows=[]
for i,pair in enumerate(pairs):
 markers=sum(v==1 for v in pair['input'][0])
 rows.append({'index':i,'markers':markers,'self_check':m.self_check(pair['input']),'output_shape':[len(pair['output']),len(pair['output'][0])]})
k0=next((i,pair) for i,pair in enumerate(pairs) if sum(v==1 for v in pair['input'][0])==0)
requested={'grid_h':10,'grid_w':14,'k_count':1,'n_objects':2}
g=m.generate(123,4,difficulty='hard',**requested)
actual={'grid_h':len(g),'grid_w':len(g[0]),'k_count':sum(v==1 for v in g[0]),'n_objects':components7(g)}
counts=Counter()
for band in ('easy','medium','hard'):
 for i in range(200):
  x=m.generate(9000+i,i,difficulty=band)
  counts[(band,sum(v==1 for v in x[0]))]+=1
report={'schema':'audit-49a0b77dcc7f-v1','task_id':T,'generator_sha256':sha(p),'generator_version':m.VERSION,
 'canonical_pairs':rows,'zero_marker_pair_index':k0[0],
 'zero_marker_input':k0[1]['input'],'zero_marker_expected_output':k0[1]['output'],
 'override_probe':{'seed':123,'sample_index':4,'difficulty':'hard','requested':requested,'actual':actual,'input':g,'self_check':m.self_check(g)},
 'sample_panel':{'per_band':200,'total':600,'marker_count_histogram':{f'{b}:{k}':v for (b,k),v in sorted(counts.items())},'zero_marker_draws':sum(v for (b,k),v in counts.items() if k==0)},
 'finding':'Canonical k=0 is rejected and absent from 600 defaults; advertised exact controls are ignored by layout draws.'}
out=Path('/mnt/data/arc_review_round5/WORK/checks/audit/49a0b77dcc7f/probe.json');out.write_text(json.dumps(report,indent=2)+'\n')
Path('/mnt/data/arc_review_round5/WORK/checks/audit/49a0b77dcc7f/input.json').write_text(json.dumps(k0[1]['input'],indent=2)+'\n')

# 1c8
T='1c8c9bef01c5'; m,p=load(T); pairs=canonical_pairs(T,root=ROOT)
rows=[]
for i,pair in enumerate(pairs):
 source_rows=[r for r,row in enumerate(pair['input']) if 7 in row]
 rows.append({'index':i,'source_rows':source_rows,'self_check':m.self_check(pair['input']),'input_shape':[len(pair['input']),len(pair['input'][0])],'output_changes':sum(a!=b for ra,rb in zip(pair['input'],pair['output']) for a,b in zip(ra,rb))})
# Check dead advertised controls on a panel.
dead={}
for axis,values in [('anchor_corner',(False,True)),('asymmetry_force',(False,True))]:
 same=0
 examples=[]
 for i in range(50):
  a=m.generate(12000+i,i,**{axis:values[0]}); b=m.generate(12000+i,i,**{axis:values[1]})
  same += a==b
  if len(examples)<1 and a==b: examples.append({'seed':12000+i,'sample_index':i,'input':a})
 dead[axis]={'identical_pairs':same,'total':50,'example':examples}
report={'schema':'audit-1c8c9bef01c5-v1','task_id':T,'generator_sha256':sha(p),'generator_version':m.VERSION,
 'canonical_pairs':rows,'canonical_rejected':sum(bool(r['self_check']) for r in rows),'canonical_total':len(rows),
 'canonical_input':pairs[0]['input'],'canonical_expected_output':pairs[0]['output'],
 'dead_axis_panel':dead,
 'finding':'The validator rejects canonical source rows; advertised anchor/asymmetry controls are behaviorally dead on the sampled panel.'}
out=Path('/mnt/data/arc_review_round5/WORK/checks/audit/1c8c9bef01c5/probe.json');out.write_text(json.dumps(report,indent=2)+'\n')
Path('/mnt/data/arc_review_round5/WORK/checks/audit/1c8c9bef01c5/input.json').write_text(json.dumps(pairs[0]['input'],indent=2)+'\n')
print(json.dumps({'49a':report if False else 'written','1c8':'written'}))
