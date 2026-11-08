"""Bounded replayable lesson/rival audit; no universal uniqueness claim."""
from pathlib import Path
import argparse,importlib.util,json,hashlib
from functools import lru_cache
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_analogy_audit_adapter_'+str(HERE),HERE/'adapter.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.engine
RIVALS=('identity','first_reference','second_reference','largest_reference','route_only','reflection_only','uniform_inverse','full_box','fixed_color','opposite_view')
@lru_cache(maxsize=256)
def _info(key):return m.analyze([list(row) for row in key])
def rival(g,mode,name):
 info=_info(tuple(map(tuple,g)));q=info['query'];ref=info['reference'];n=len(q)
 if name=='opposite_view':return m.render(q,info['completed'],'changes_only' if mode=='complete' else 'complete')
 if name=='identity':out=q
 elif name=='first_reference':out=ref[0]
 elif name=='second_reference':out=ref[1]
 elif name=='largest_reference':out=max(ref,key=lambda p:sum(v!=0 for row in p for v in row))
 elif name in ('route_only','reflection_only'):
  try:out=(m.line_complete if name=='route_only' else m.reflect_complete)(q)
  except ValueError:out=q
 elif name=='uniform_inverse':
  color=next(v for row in q for v in row if v);out=[[0 if v else color for v in row] for row in q]
 elif name=='full_box':
  pts=[(r,c) for r in range(n) for c in range(n) if q[r][c]];rs,cs=zip(*pts);color=q[pts[0][0]][pts[0][1]]
  out=[[q[r][c] or (color if min(rs)<=r<=max(rs) and min(cs)<=c<=max(cs) else 0) for c in range(n)] for r in range(n)]
 elif name=='fixed_color':out=[[9 if v else 0 for v in row] for row in info['completed']]
 else:raise ValueError(name)
 return m.render(q,out,mode)
def run(seeds):
 counts={'episodes':0,'pairs':0,'size_30_pairs':0,'matched_inputs':0,'harmful_survivors':0};witness={};fail=[]
 for seed in range(seeds):
  banks=[a.generate(seed,{'view':mode},6,4) for mode in m.SETTINGS]
  assert [p['input'] for sp in ('train','test') for p in banks[0][sp]]==[p['input'] for sp in ('train','test') for p in banks[1][sp]];counts['matched_inputs']+=10
  for mode,bank in zip(m.SETTINGS,banks):
   labels={name:[rival(p['input'],mode,name) for p in bank['train']+bank['test']] for name in RIVALS}
   for d in range(2,7):
    counts['episodes']+=1;counts['pairs']+=d+4;counts['size_30_pairs']+=1
    for name,ys in labels.items():
     fit=all(ys[i]==p['output'] for i,p in enumerate(bank['train'][:d]));harm=any(ys[6+i]!=p['output'] for i,p in enumerate(bank['test']))
     if fit and harm:fail.append({'seed':seed,'setting':mode,'demos':d,'rival':name});counts['harmful_survivors']+=1
     for i,p in enumerate(bank['train'][:d]):
      key=mode+':'+name
      if ys[i]!=p['output'] and key not in witness:witness[key]={'seed':seed,'settings':{'view':mode},'pair_index':i,'input':p['input'],'output':p['output'],'rival_output':ys[i]}
 return {'schema':'bounded-framed-analogy-audit-v1','status':'passed' if not fail else 'failed','seeds':seeds,'counts':counts,'rivals':list(RIVALS),'witnesses':witness,'failures':fail,'source_sha256':hashlib.sha256((HERE/'engine.py').read_bytes()).hexdigest(),'limits':'Finite declared operators and rivals; original-label fidelity is checked separately through protected Racket.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);args=p.parse_args();m.integer(args.seeds,1,256,'seeds');r=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('witnesses','rivals')}));raise SystemExit(bool(r['failures']))
