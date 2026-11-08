"""Finite source-local rivals evaluated on demonstrations only for teaching."""
from pathlib import Path
import importlib.util,sys,hashlib,copy
from collections import Counter
from functools import lru_cache
@lru_cache(None)
def load(p):
 p=Path(p);n='_seventh_rivals_'+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def predictions(a,g,mode):
 t=a.TASK;b=a.BASE/'seventh-banks';result={}
 if t=='8e5c0c38':
  if mode=='horizontal':return a.BANKS[0].BANKS[1].engine.rivals(g,mode)
  m=load(b/'extra0/workspace/parametric/audit.py');return {n:m.predict(g,mode,n)for n in m.rival_names(mode)}
 if t=='edb79dae':
  m=a.BANKS[0].m;return {n:m.predict(g,n)for n in m.RIVALS if n!=mode}
 if t=='c7f57c3e':return a.BANKS[1].engine.rivals(g,'exchange'if mode=='swap'else mode)
 if t=='f560132c':
  P=a.BANKS[0].P;y=P.solve(g,'pack_only');result={n:P.solve(g,n)for n in P.INTERNAL_SETTINGS if n!=mode}
  F=a.BANKS[1].family
  result.update(all_seams=F.mark(y,threshold=2),diagonal_junctions=F.mark(y,diagonal=True))
  return result
 if t=='dbff022c':
  if mode!='highlight_dominant_fill':
   m=load(b/'current/workspace/parametric/audit.py');return {n:m.predict(g,n,{'fill_scope':mode})for n in m.RIVALS if n!=mode}
  m=a.BANKS[0].model;d=m.analyze(g);y=m.solve(g,'all');changes=[(r,c,v)for r,row in enumerate(y)for c,v in enumerate(row)if v!=g[r][c]];totals=Counter(v for r,c,v in changes);mapping=d['legend']['mapping']
  groups=[z for z in d['regions']if z['color']in mapping];counts=Counter(mapping[z['color']]for z in groups)
  raw=Counter(v for row in g for v in row if v in mapping)
  selectors={'raw_frame':mapping[max(raw,key=lambda v:(raw[v],v))], 'most_holes':max(counts,key=lambda v:(counts[v],v)), 'smallest_total':min(totals,key=lambda v:(totals[v],v)), 'largest_single_hole':mapping[max(groups,key=lambda z:z['area'])['color']], 'first_mapping':mapping[min(mapping)], 'all_filled':None}
  for n,chosen in selectors.items():
   out=copy.deepcopy(y)
   for r,c,v in changes:
    if chosen is None or v==chosen:out[r][c]=9
   result[n]=out
  result['fill_only']=y;result['identity']=copy.deepcopy(g);return result
 return result
