import hashlib,json
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CANON=ROOT/'repo/shared/data/base/solutions/training/9841fdad__ae70dcf677ff.json'
def majority_background_rival(g):
 h,w=len(g),len(g[0]);f=g[0][0];sep=next(c for c in range(1,w-1) if all(g[r][c]==f for r in range(h)))
 lw=sep-1; bg=Counter(g[r][c] for r in range(1,h-1) for c in range(1,sep)).most_common(1)[0][0]
 seen=set();comps=[]
 for r in range(1,h-1):
  for c in range(1,sep):
   if (r,c) in seen or g[r][c]==bg:continue
   col=g[r][c];q=[(r,c)];seen.add((r,c));cells=[]
   while q:
    rr,cc=q.pop();cells.append((rr,cc))
    for nr,nc in [(rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)]:
     if 1<=nr<h-1 and 1<=nc<sep and (nr,nc) not in seen and g[nr][nc]==col:seen.add((nr,nc));q.append((nr,nc))
   r1=min(x[0] for x in cells);r2=max(x[0] for x in cells);c1=min(x[1] for x in cells)-1;c2=max(x[1] for x in cells)-1
   ow=c2-c1+1;lm=c1;rm=lw-1-c2;rs=sep+1;re=w-2
   pc1=rs+lm if lm<=rm else re-rm-ow+1
   pc2=re-rm if lm==rm else pc1+ow-1
   comps.append((r1,r2,pc1,pc2,col))
 out=[row[:] for row in g]
 for r in range(h):
  for c in range(sep+1,w-1):
   for r1,r2,c1,c2,col in comps:
    if r1<=r<=r2 and c1<=c<=c2:out[r][c]=col;break
 return out
p=json.loads((OUT/'probe-results.json').read_text());r=json.loads((OUT/'racket.json').read_text());g=p['generated_corner_witness']['input'];actual=r['results'][0]['output'];rival=majority_background_rival(g)
canonical=json.loads(CANON.read_text());pairs=canonical['visible_context']['train'][:]
for i,pair in enumerate(canonical['visible_context']['test_inputs']):pairs.append({'input':pair['input'],'output':canonical['verification']['expected_test_outputs'][i]})
fits=[majority_background_rival(pair['input'])==pair['output'] for pair in pairs]
assert all(fits),fits
witness={'task_id':'ae70dcf677ff','classification':'reproduced generated-domain background defect','example_origin':'generated','validator_errors':p['generated_corner_witness']['self_check'],'seed':0,'sample_index':0,'difficulty':None,'overrides':{},'input':g,'actual_racket_output':actual,'rival_name':'majority_left_background_then_reference_projection','rival_output':rival,'rival_canonical_fit':{'fits':sum(fits),'denominator':len(fits),'pair_policy':'all 2 canonical train pairs plus 1 canonical verification pair'},'different_cells':sum(a!=b for ar,br in zip(actual,rival) for a,b in zip(ar,br)),'source_identity':dict(p['source_identity'],rule_text_sha256=r['rule_text_sha256'],executed_rule_hash=r['executed_rule_hash']),'racket_command':{'cwd':'packet_root','effective_cwd':'repo','argv':['env','PYTHONDONTWRITEBYTECODE=1','python3','run_with_racket.py','python3','-m','arcpuzzles','apply','ae70dcf677ff','--input','../checks/audit/ae70dcf677ff/input.json','--out','../checks/audit/ae70dcf677ff/racket.json'],'exit_code':0},'scope':'Canonical fit uses stored canonical labels. Only this generated witness was newly Racket-labelled. Rival is a task-domain diagnostic, not proposed replacement authority.'}
(OUT/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
print('canonical fits',sum(fits),'/',len(fits),'witness different cells',witness['different_cells'],'racket valid',r['results'][0]['valid_output'])
