"""Exact incumbent programs and broad input domains with source-local rule ports."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_twelfth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
C=BANKS[0]
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 i=selected(settings);mode=CONFIG['modes'][i];old=CONFIG['banks'][0]['config']
 if mode in old['parameters'][CONFIG['key']]:return C.program(settings)
 source=C.program(old['default'])
 if TASK=='7c66cb00':
  a='(- (second b) (obj-r2 o))';assert source.count(a)==1;return source.replace(a,'(- (first b) (obj-r1 o))')
 if TASK=='bf45cf4b':
  a='   (for/list ([r (in-range (* (rows mask) (rows tile)))])';start=source.index(a);body=source[start:].strip()[:-3]
  if mode=='largest_enclosed':
   return source[:start]+'(define expanded '+body+')\n(define holes (filter (lambda (o) (and (> (obj-r1 o) 0) (> (obj-c1 o) 0) (< (obj-r2 o) (- (rows expanded) 1)) (< (obj-c2 o) (- (cols expanded) 1)))) (objects (map (lambda (row) (map (lambda (v) (if (= v bg) 10 bg)) row)) expanded) bg)))\n(if (null? holes) expanded (recolor-cells expanded (obj-cells (pick-max holes obj-size)) (obj-color mo))))))\n'
  return source[:start]+'(define expanded '+body+')\n(define groups-out (objects (map (lambda (row) (map (lambda (v) (if (= v bg) bg 10)) row)) expanded) bg))\n(define maximum (apply max (map obj-size groups-out)))\n(for/fold ([out expanded]) ([o groups-out] #:when (= (obj-size o) maximum)) (recolor-cells out (obj-cells o) 9)))))\n'
 raise ValueError('unknown extension')
def predict(g,index):
 mode=CONFIG['modes'][index]
 if TASK=='6ffbe589':return C.solve(g,mode)
 if TASK=='7b5033c1':return C.predict(g,mode)
 if TASK=='981571dc':return C.G.solve(g,mode)
 if TASK=='7c66cb00':
  if mode!='ceiling':return C.predict(g,mode)
  info=C.analyze(g);out=copy.deepcopy(g)
  for d in info['deliveries']:
   if d['band']:
    for r,c in d['source']:out[r][c]=g[0][0]
  for d in info['deliveries']:
   if d['band']:
    shift=d['band']['start']-min(r for r,c in d['source'])
    for r,c in d['source']:out[r+shift][c]=d['band']['rail']
  return out
 if TASK=='bf45cf4b':
  if mode=='largest_enclosed':
   out=C.G.solve(g,'all');z=C.G.parse(g);bg=z['background'];parts=C.G.components((r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v==bg);holes=[q for q in parts if all(0<r<len(out)-1 and 0<c<len(out[0])-1 for r,c in q)]
   if holes:
    color=next(v for row in z['mask']for v in row if v!=bg)
    for r,c in max(holes,key=len):out[r][c]=color
   return out
  if mode!='highlight_largest':return C.G.solve(g,mode)
  out=C.G.solve(g,'all');bg=C.G.parse(g)['background'];groups=C.G.components((r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v!=bg);maximum=max(map(len,groups))
  for cells in groups:
   if len(cells)==maximum:
    for r,c in cells:out[r][c]=9
  return out
@lru_cache(maxsize=64)
def inputs(seed):
 ep=C.generate(seed,CONFIG['banks'][0]['config']['default'],6,4)
 pack=lambda p,b:(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 tr=[pack(p,0)for p in ep['train']];te=[pack(p,0)for p in ep['test']];rejected=[]
 bank=seed%len(BANKS)
 if bank:
  b=CONFIG['banks'][bank]
  try:
   other=BANKS[bank].generate(seed,b['config']['default'],6,4);new=[]
   for p in other['test']:
    try:new.append(pack(p,bank))
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_domain'))
   if new:
    seen={json.dumps(x[0])for x in new};te=(new+[x for x in te if json.dumps(x[0])not in seen])[:4]
  except (ValueError,TypeError,IndexError,KeyError,AssertionError,RuntimeError)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_sampler'))
 # Select two incumbent examples that separate every active setting; this preserves
 # the incumbent six-scene teaching pool and does not use private query outputs.
 if TASK=='bf45cf4b':
  # Supplement teaching with compatible incoming demo constructors. Never inspect
  # a query label to choose the teaching prefix.
  for attempt in range(12):
   bi=1 if attempt%2 else len(BANKS)-1
   other=BANKS[bi].generate(seed+attempt*100003,CONFIG['banks'][bi]['config']['default'],6,4)
   for p in other['train']:
    try:
     x=pack(p,bi)
     if json.dumps(x[0])not in {json.dumps(y[0])for y in tr+te}:tr.append(x)
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration):pass
 masks=[];needed=0
 if TASK=='bf45cf4b':
  for x in tr:
   g=x[0];out=C.G.solve(g,'all');z=C.G.solve(g,'largest');bg=C.G.parse(g)['background'];groups=C.G.components((r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v!=bg)
   rs=[]
   for mode in ['all','largest']:
    for rival in C.G.RIVALS:rs.append((C.G.solve(g,mode,rival=rival),C.G.solve(g,mode)))
   for kind in ['preexpansion','samecolor','first','last']:
    if kind=='preexpansion':cells={(r,c)for r,row in enumerate(z)for c,v in enumerate(row)if v!=bg}
    elif kind=='samecolor':
     gs=sum([C.G.components((r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v==color)for color in set(v for row in out for v in row)-{bg}],[]);cells={p for q in gs if len(q)==max(map(len,gs))for p in q}
    else:cells=set(groups[0 if kind=='first'else -1])
    rs.append(([[9 if(r,c)in cells else v for c,v in enumerate(row)]for r,row in enumerate(out)],x[1][CONFIG['modes'].index('highlight_largest')]))
   for rival in BANKS[1].RIVALS:rs.append((BANKS[1].predict(g,rival),predict(g,CONFIG['modes'].index('largest_enclosed'))))
   mask=sum(1<<k for k,(a,b)in enumerate(rs)if a!=b);masks.append(mask);needed|=mask
 def useful(i,j):return TASK!='bf45cf4b' or masks[i]|masks[j]==needed
 pairs=[(i,j)for i in range(len(tr))for j in range(i+1,len(tr))if useful(i,j)]
 best=next(((i,j)for i,j in pairs if all(tr[i][1][a]!=tr[i][1][b]or tr[j][1][a]!=tr[j][1][b]for a in range(len(CONFIG['modes']))for b in range(a))),None)
 if best is None:raise ValueError('no two-demo separating curriculum')
 order=list(best)+[i for i in range(len(tr))if i not in best];tr=[tr[i]for i in order[:6]]
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**128-1 if TASK=='7c66cb00' else 2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:twelfth-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
