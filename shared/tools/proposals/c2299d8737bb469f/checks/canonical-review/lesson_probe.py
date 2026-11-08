import json,sys,importlib.util,itertools,collections,hashlib
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parent.parent/'repo'
sys.path.insert(0,str(root/'shared/runtime'))
p=here/'generator_v3_1_0.py';spec=importlib.util.spec_from_file_location('g',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
r=json.loads((here/'report.json').read_text());samples=r['generated']
def lesson(ids,q):
 demos=[dict(input=samples[i]['input'],output=samples[i]['output']) for i in ids]
 query=dict(input=samples[q]['input'],output=samples[q]['output'])
 return dict(seed=0,difficulty='medium',demo_indices=ids,query_index=q,demos=demos,query=query,rival_query_output=samples[q]['rival_output'],rival_fits_all_demos=all(samples[i]['rival_matches'] for i in ids),rival_disagrees_query=not samples[q]['rival_matches'],original_lesson_hook_errors=g.lesson_identifiable(demos,query))
reflections={'flip_lr','flip_ud','transpose','anti_transpose'}
swap={'transpose','anti_transpose','rot_cw','rot_ccw'}
count=0;first=None
for perm in itertools.permutations(g.SYMMETRIES):
 if not all(0<sum(perm[(i+j)%8] in swap for j in range(4))<4 for i in range(8)):continue
 if not all(2<=sum(perm[(i+j)%8] in swap for j in range(5))<=3 and sum(perm[(i+j)%8] not in reflections for j in range(5))>=2 for i in range(8)):continue
 count+=1
 if first is None:first=perm
out=dict(source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),authority='Actual canonical Racket, inherited directly from racket_receipt.json',production=lesson([1,2,3,4],5),rotation=lesson([1,2,3,4],0),proposed_constraints_valid_permutations=count,first_valid_permutation=first)
(here/'lesson_witness.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['production','rotation']}))
for k in ['production','rotation']:print(k,{key:value for key,value in out[k].items() if key not in ['demos','query','rival_query_output']})
