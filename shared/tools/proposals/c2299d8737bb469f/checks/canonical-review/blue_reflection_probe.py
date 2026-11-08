import json,sys,importlib.util,hashlib,collections,itertools
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE.parent.parent/'repo'
sys.path.insert(0,str(root/'shared/runtime'));sys.path.insert(0,str(root/'src'))
p=HERE/'generator_v3_1_0.py'; sourcehash=hashlib.sha256(p.read_bytes()).hexdigest()
assert sourcehash=='36c7be0c8dc4b1e43b190809566505af62f88fd8fe031e5c966efea3904c8797'
spec=importlib.util.spec_from_file_location('g',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
from arcpuzzles import Catalog
refl=('flip_lr','flip_ud','transpose','anti_transpose')
def rival(x):
 a=g._analyze(x)
 matches=[s for s in refl if g._arrangement(s,a['corners']).index(1)==a['signature'].index(1)]
 assert len(matches)==1
 return g._transform_grid(a['panel'],matches[0]),matches[0]
rows=[]
for line in (root/'shared/data/canonical/puzzles.jsonl').open():
 if 'c5f62271ea44' not in line: continue
 row=json.loads(line)
 if row['task_id']=='c5f62271ea44':rows.append(row)
pairs=[p for row in rows for split in ['train','test'] for p in row[split] if 'output' in p]
generated=[dict(seed=0,sample_index=i,difficulty='medium',input=g.generate(0,i,difficulty='medium')) for i in range(8)]
inputs=[p['input'] for p in pairs]+[p['input'] for p in generated]
receipt=Catalog(root).apply(g.TASK_ID,inputs,check_generator_domain=True)
(HERE/'racket_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
canonical=[];witnesses=[]
for i,(x,result) in enumerate(zip(inputs,receipt['results'])):
 y=result['output']; pred,rs=rival(x);a=g._analyze(x)
 actual=[s for s in g.SYMMETRIES if g._transform_grid(a['panel'],s)==y]
 record=dict(input_sha256=result['input_sha256'],actual_symmetries=actual,rival_symmetry=rs,rival_matches=pred==y,corners=a['corners'],signature=a['signature'])
 if i<len(pairs):
  record['matches_stored_canonical_output']=y==pairs[i]['output'];canonical.append(record)
 else:
  record.update(generated[i-len(pairs)]);record.update(output=y,rival_output=pred)
  witnesses.append(record)
# Pure schedule census: since distinct marker colors ensure all 8 outputs differ,
# this rival fits a pair iff its scheduled symmetry is a reflection.
counts=collections.Counter();first=None
for seed in range(128):
 order=[g.schedule_profile(seed,i) for i in range(8)]
 for start in range(8):
  syms=[order[(start+j)%8] for j in range(5)]
  for query_index in range(5):
   demos=[s for j,s in enumerate(syms) if j!=query_index]
   ambiguous=all(s in refl for s in demos) and syms[query_index] not in refl
   if ambiguous:
    counts['ambiguous_rotations']+=1
    if query_index==4: counts['ambiguous_production']+=1
    if first is None: first=dict(seed=seed,start=start,query_index=query_index,syms=syms)
  counts['lessons']+=1
report=dict(source_sha256=sourcehash,rival='blue_corner_reflection',definition='Choose unique reflection matching only source and target blue corners, transport whole panel',canonical=canonical,generated=witnesses,schedule_census=dict(counts=counts,first=first,seeds=[0,127],starts=[0,7],label_basis='Exact distinct-corner D4 action; actual Racket verified for eight seed-0 generated samples'))
(HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(source_sha256=sourcehash,canonical_fit=sum(v['rival_matches'] for v in canonical),canonical_rows=len(canonical),generated_disagreements=[(v['seed'],v['sample_index'],v['actual_symmetries'],v['rival_symmetry']) for v in witnesses if not v['rival_matches']],schedule_census=report['schedule_census']),indent=2))
