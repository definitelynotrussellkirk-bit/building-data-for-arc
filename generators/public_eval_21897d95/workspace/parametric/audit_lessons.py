"""Replayable bounded adversarial audit of region routing and control ink."""
from pathlib import Path
import argparse,importlib.util,json,hashlib
from functools import lru_cache
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_arrows_audit_adapter_'+str(HERE),HERE/'adapter.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.engine
RIVALS=('identity','clean_only','paint_source','global_color','no_turn','opposite_turn','half_turn','explicit_only','opposite_ink','cascade','reverse_ray','last_hit','eight_connected','keep_symbols')
@lru_cache(maxsize=256)
def _info(key):return m.analyze([list(row) for row in key])
def rival(g,mode,name):
 info=_info(tuple(map(tuple,g)));clean=info['clean'];h,w=len(clean),len(clean[0])
 if name=='identity':return [row[:] for row in g]
 if name=='clean_only':return m.rotate(clean,info['turn'])
 if name=='paint_source':return m.render(info,mode,target_source=True)
 if name=='global_color':return m.render(info,mode,color_global=True)
 if name=='no_turn':return m.render(info,mode,turn_override=0)
 if name=='opposite_turn':return m.render(info,mode,turn_override=-info['turn'])
 if name=='half_turn':return m.render(info,mode,turn_override=2)
 if name=='opposite_ink':return m.render(info,'source_color' if mode=='payload' else 'payload')
 if name=='cascade':return m.render(info,mode,cascade=True)
 if name=='keep_symbols':return m.render(info,mode,keep_symbols=g)
 out=[row[:] for row in clean]
 lookup={p:i for i,obj in enumerate(info['regions']) for p in obj['cells']}
 for arrow in info['arrows']:
  if name=='explicit_only' and arrow['payload']==arrow['source']:continue
  cells=info['regions'][arrow['target']]['cells']
  if name in ('reverse_ray','last_hit'):
   r,c=arrow['center'];dr,dc=arrow['direction']
   if name=='reverse_ray':dr,dc=-dr,-dc
   hits=[];r+=dr;c+=dc
   while 0<=r<h and 0<=c<w:
    if clean[r][c]!=arrow['source']:hits.append((r,c))
    r+=dr;c+=dc
   if not hits:continue
   hit=hits[-1] if name=='last_hit' else hits[0];cells=info['regions'][lookup[hit]]['cells']
  elif name=='eight_connected':
   hit=arrow['hit'];co=clean[hit[0]][hit[1]];seen={hit};stack=[hit]
   while stack:
    r,c=stack.pop()
    for dr in (-1,0,1):
     for dc in (-1,0,1):
      p=(r+dr,c+dc)
      if 0<=p[0]<h and 0<=p[1]<w and p not in seen and clean[p[0]][p[1]]==co:seen.add(p);stack.append(p)
   cells=seen
  elif name!='explicit_only':raise ValueError(name)
  color=arrow['payload'] if mode=='payload' else arrow['source']
  for r,c in cells:out[r][c]=color
 return m.rotate(out,info['turn'])
def run(seeds):
 counts={'episodes':0,'pairs':0,'size_30_pairs':0,'matched_inputs':0,'harmful_survivors':0};witness={};fail=[]
 for seed in range(seeds):
  banks=[a.generate(seed,{'ink':mode},6,4) for mode in m.SETTINGS]
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
      if ys[i]!=p['output'] and key not in witness:witness[key]={'seed':seed,'settings':{'ink':mode},'pair_index':i,'input':p['input'],'output':p['output'],'rival_output':ys[i]}
 return {'schema':'bounded-region-arrows-audit-v1','status':'passed' if not fail else 'failed','seeds':seeds,'counts':counts,'rivals':list(RIVALS),'witnesses':witness,'failures':fail,'source_sha256':hashlib.sha256((HERE/'engine.py').read_bytes()).hexdigest(),'limits':'Finite declared rivals; original-label fidelity and retained witnesses need protected Racket execution.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);args=p.parse_args();m.integer(args.seeds,1,256,'seeds');r=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('witnesses','rivals')}));raise SystemExit(bool(r['failures']))
