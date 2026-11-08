import json,sys,importlib.util,hashlib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;root=HERE.parents[2]/'repo';TASK='0727bca3d518'
sys.path.insert(0,str(root/'shared/runtime'));sys.path.insert(0,str(root/'src'))
p=root/f'generators/{TASK}/generator.py';sh=hashlib.sha256(p.read_bytes()).hexdigest()
assert sh=='0c26f5935d057f8f3b77c603b6a5dd930444625eba6758364915be246007e325'
spec=importlib.util.spec_from_file_location('g',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
from arcpuzzles import Catalog
rows=[]
for line in (root/'shared/data/canonical/puzzles.jsonl').open():
 if TASK not in line:continue
 row=json.loads(line)
 if row['task_id']==TASK:rows.append(row)
cases=[]
for v,row in enumerate(rows):
 for split in ['train','test']:
  ps=row[split];ps=[ps] if isinstance(ps,dict) else ps
  for i,pair in enumerate(ps):
   if 'output' in pair:cases.append(dict(kind='canonical',variant=v,split=split,index=i,input=pair['input'],stored_output=pair['output']))
for band in ['easy','medium','hard']:
 for seed in range(8):cases.append(dict(kind='default',seed=seed,sample_index=0,difficulty=band,input=g.generate(seed,0,difficulty=band)))
for texture in g.HELPFUL_TEXTURES:
 for d1 in range(1,4):
  for d2 in range(1,4):
   opts=dict(panel_h=7,depth1=d1,depth2=d2,texture=texture)
   cases.append(dict(kind='override',seed=0,sample_index=0,overrides=opts,input=g.generate(0,0,**opts)))
def panels(x):
 cuts=[-1]+[c for c in range(len(x[0])) if all(r[c]==9 for r in x)]+[len(x[0])]
 return [[r[a+1:b] for r in x] for a,b in zip(cuts,cuts[1:]) if b>a+1]
def square_depth(p):
 h,w=len(p),len(p[0]);dp=[[0]*(w+1) for _ in range(h+1)];best=0
 for r in range(h):
  for c in range(w):
   if p[r][c] not in (0,9):dp[r+1][c+1]=1+min(dp[r][c],dp[r][c+1],dp[r+1][c]);best=max(best,dp[r+1][c+1])
 return (best+1)//2
receipt=Catalog(root).apply(TASK,[c['input'] for c in cases],check_generator_domain=True)
(HERE/'racket_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
counts=collections.Counter()
for case,result in zip(cases,receipt['results']):
 case.update(output=result['output'],input_sha256=result['input_sha256'])
 ps=panels(case['input'])[:2];case['square_rival_output']=[[square_depth(p) for p in ps]];case['mirror_output']=[[g._depth(p) for p in ps]]
 case['rival_match']=case['output']==case['square_rival_output'];counts[case['kind']+'_cases']+=1;counts[case['kind']+'_rival_matches']+=case['rival_match']
 counts['mirror_matches']+=case['output']==case['mirror_output']
 if case['kind']=='canonical':case['canonical_stored_match']=case['output']==case['stored_output']
controls=[]
for opts in [dict(panel_h=4),dict(panel_h=9),dict(panel_h=10),dict(depth1=4,panel_h=7),dict(depth1=0),dict(depth1=True),dict(depth1=1.5),dict(texture='not_a_texture'),dict(unknown_axis=1)]:
 try:
  x=g.generate(0,0,**opts);result=dict(accepted=True,height=len(x),depths=[g._depth(p) for p in panels(x)[:2]])
 except Exception as e:result=dict(accepted=False,error=type(e).__name__+': '+str(e))
 controls.append(dict(overrides=opts,**result))
report=dict(task_id=TASK,source_sha256=sh,version=g.VERSION,rule_hash=receipt['executed_rule_hash'],rule_text_sha256=receipt['rule_text_sha256'],counts=counts,cases=cases,controls=controls,rival_definition='Per panel ceil(side of largest fully occupied axis-aligned square /2), merge nonzero non9 colors; first2 panels only')
(HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(source_sha256=sh,rule_hash=report['rule_hash'],counts=counts,canonical=[{k:c[k] for k in ['split','index','output','square_rival_output','canonical_stored_match']} for c in cases if c['kind']=='canonical'],controls=controls),indent=2))
