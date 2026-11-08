from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent; R=D.parents[2]/'repo';sys.path.insert(0,str(R/'shared/runtime'))
from reviewer_support import canonical_pairs,load_selected_generator
G,S,H=load_selected_generator('4e6862c442fd',root=R)
pairs=canonical_pairs(G.TASK_ID,root=R)
canon=[]
for p in pairs:
 a=G._analyze(p['input']);canon.append({k:a[k] for k in ['errors','source_basis','target_basis','relative_transform','motif_id','motif','source_origin','target_origin']})
print('hash',H);print('canonical',json.dumps(canon,indent=2));print('basismatrices',G._BASIS_MATRICES)
for i in range(8):
 a=G._analyze(G.generate(0,i)); print(i,a['motif_id'],a['relative_transform'],a['source_basis'],a['target_basis'])
ledger=next(json.loads(line) for line in (R/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id')==G.TASK_ID)
(D/'source.py').write_bytes(S.read_bytes());(D/'rule.rkt').write_text(ledger['program_solution'])
(D/'canonical-analysis.json').write_text(json.dumps(dict(source_sha256=H,canonical=canon),indent=2)+'\n')
print('rule',ledger['program_solution'])

def motif_lookup_rival(grid):
 # Source-frame markers are read; TARGET DIRECTION markers 6/7 are never read.
 # Use the exact default curriculum's catalogue-to-D4 association instead.
 pos={v:(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v in (2,3,4,5)}
 origin=pos[2];target=pos[5]
 basis=tuple((pos[v][0]-origin[0],pos[v][1]-origin[1]) for v in (3,4))
 motifcells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8]
 offsets=[(r-origin[0],c-origin[1]) for r,c in motifcells]
 local=tuple(sorted((dr*basis[0][0]+dc*basis[0][1],dr*basis[1][0]+dc*basis[1][1]) for dr,dc in offsets))
 motifid={tuple(sorted(m)):i for i,m in enumerate(G._MOTIFS)}[local]
 matrix=G._BASIS_MATRICES[motifid]
 out=[row[:] for row in grid]
 for dr,dc in offsets:
  r=target[0]+matrix[0][0]*dr+matrix[0][1]*dc
  c=target[1]+matrix[1][0]*dr+matrix[1][1]*dc
  if 0<=r<len(out) and 0<=c<len(out[0]):out[r][c]=8
 return out

cases=[]
for band in (None,'easy','medium','hard'):
 for seed in range(8):
  for i in range(8):
   g=G.generate(seed,i,difficulty=band);a=G._analyze(g)
   assert a['motif_id']==a['relative_transform']
   assert motif_lookup_rival(g)==G.rule_mirror(g)
   cases.append((band,seed,i))
canonicalfits=[motif_lookup_rival(p['input'])==p['output'] for p in pairs]
print('Default rival matches',len(cases),'canonical matches',canonicalfits)
# Change target orientation alone in parameter space; choose an exact lawful
# generated example whose intended and rival target cells are all empty/inbounds.
for seed in range(32):
 grid=G.generate(seed,0,source_basis=0,target_basis=0,motif_id=0,grid_h=12,grid_w=18)
 true=G.rule_mirror(grid);rival=motif_lookup_rival(grid)
 if true==rival:continue
 a=G._analyze(grid)
 wrong=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if rival[r][c]!=v]
 if len(wrong)==3 and all(grid[r][c]==0 for r,c in wrong):break
else:raise AssertionError('no compact counterexample')
repro=dict(seed=seed,sample_index=0,overrides=dict(source_basis=0,target_basis=0,motif_id=0,grid_h=12,grid_w=18))
(D/'input.json').write_text(json.dumps(grid)+'\n');(D/'mirror.json').write_text(json.dumps(true)+'\n');(D/'rival.json').write_text(json.dumps(rival)+'\n')
summary=dict(source_sha256=H,rule_hash=G.RULE_HASH,rule_text_sha256=hashlib.sha256((D/'rule.rkt').read_bytes()).hexdigest(),reproducer=repro,self_check=G.self_check(grid),strict_canonical_like=G.strict_canonical_like(grid),observed=G.observe_overrides(grid),semantic_observables=G.semantic_observables(grid),default_cases=len(cases),default_rival_matches=len(cases),default_support_proof='In every _PROFILES row, motif_id == relative_transform; defaults preserve profile motif and target basis relation.',canonical_rival_matches=canonicalfits,intended_changed=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if true[r][c]!=v],rival_changed=wrong,output_disagreements=[(r,c,rival[r][c],true[r][c]) for r,row in enumerate(grid) for c,v in enumerate(row) if rival[r][c]!=true[r][c]])
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
rr=json.loads((D/'racket.json').read_text())
assert rr['results'][0]['error'] is None and rr['results'][0]['output']==true and true!=rival
assert rr['executed_rule_hash']==G.RULE_HASH
summary['racket_equals_mirror']=True;summary['racket_differs_rival']=True
summary['racket_executed_rule_hash']=rr['executed_rule_hash'];summary['racket_rule_text_sha256']=rr['rule_text_sha256']
summary['canonical_mirror_matches']=[G.rule_mirror(p['input'])==p['output'] for p in pairs]
demos=[dict(input=G.generate(0,i),output=G.rule_mirror(G.generate(0,i))) for i in range(3)]
query=dict(input=grid,output=true)
summary['lesson_identifiable']=G.lesson_identifiable(demos,query)
summary['rival_fits_three_demos']=[motif_lookup_rival(p['input'])==p['output'] for p in demos]
(D/'lesson.json').write_text(json.dumps(dict(train=demos,test=[query]),indent=2)+'\n')
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('RACKET and lesson final',json.dumps({k:summary[k] for k in ['racket_equals_mirror','racket_differs_rival','canonical_mirror_matches','lesson_identifiable','rival_fits_three_demos']}))
