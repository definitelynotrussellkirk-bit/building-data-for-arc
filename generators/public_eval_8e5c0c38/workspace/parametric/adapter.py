"""Exact incumbent rules plus source-local complementary constructors and selectors."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
from collections import Counter
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'seventh-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'seventh-banks'/bank['name']/'workspace/parametric/adapter.py';n='_seventh_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
MIN_DEMOS=3 if TASK in ('8e5c0c38','dbff022c') else 2
SETTINGS=tuple({CONFIG['key']:v}for v in CONFIG['modes'])
if TASK=='c7f57c3e':_model=BANKS[0]._model
if TASK=='dbff022c':model=BANKS[0].model
if TASK=='f560132c':P=BANKS[0].P
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 i,s=CONFIG['active'][selected(settings)]
 if i>=0:return BANKS[i].program(s)
 source=BANKS[0].program(CONFIG['banks'][0]['config']['default']).replace('(rule!', '(define incumbent',1)
 if TASK=='f560132c':
  body='''(grid-from-fn (rows completed) (cols completed) (lambda (r c)
   (define colors (remove-duplicates (for/list ((d (cons (list 0 0) cardinal-deltas))
     #:when (in-bounds? (+ r (first d)) (+ c (second d)) (rows completed) (cols completed)))
       (at completed (+ r (first d)) (+ c (second d))))))
   (if (>= (length colors) 3) 9 (at completed r c))))'''
 else:
  body='''(define changed (for*/list ((r (range (rows g))) (c (range (cols g))) #:when (not (= (at completed r c) (at g r c)))) (list r c (at completed r c))))
   (define colors (sort (remove-duplicates (map third changed)) <))
   (define (number color) (count-if (lambda (p) (= color (third p))) changed))
   (define dominant (and (pair? colors) (for/fold ((best (first colors))) ((color (rest colors))) (if (> (number color) (number best)) color best))))
   (for/fold ((out completed)) ((p changed) #:when (= (third p) dominant)) (set-cell out (first p) (second p) 9))'''
 return '(rule! (lambda (g) (let ()\n'+source+'\n(define completed (incumbent g))\n'+body+'\n)))'
def predict(i,g,s):
 m=BANKS[i];v=next(iter(s.values()))
 if TASK=='8e5c0c38':return m.table(g)[m.CONFIG['modes'].index(v)] if i==0 else m.R.solve(g,v)
 if TASK=='c7f57c3e':return m._model.solve(g,replacement=v)if i==0 else m.engine.solve(g,v)
 if TASK=='edb79dae':return (m.m if hasattr(m,'m')else m.family).predict(g,v)
 if TASK=='dbff022c':return m.model.solve(g,v)if i==0 else m.model().solve(g,fill_scope=v)if i==1 else m.family.solve(g,v)
 if TASK=='f560132c':return m.P.solve(g,v)if i==0 else m.family.solve(g,v)
def table(g):
 try:
  out=[]
  for i,s in CONFIG['active']:
   if i>=0:out.append(predict(i,g,s));continue
   y=copy.deepcopy(out[0])
   if TASK=='f560132c':
    for r,row in enumerate(y):
     for c in range(len(row)):
      colors={out[0][rr][cc]for rr,cc in ((r,c),(r-1,c),(r+1,c),(r,c-1),(r,c+1))if 0<=rr<len(y)and 0<=cc<len(row)}
      if len(colors)>=3:y[r][c]=9
   else:
    changed=[(r,c,v)for r,row in enumerate(y)for c,v in enumerate(row)if v!=g[r][c]];counts=Counter(v for r,c,v in changed)
    dominant=min(counts,key=lambda v:(-counts[v],v))if counts else None
    for r,c,v in changed:
     if v==dominant:y[r][c]=9
   out.append(y)
  return out
 except (ValueError,TypeError,KeyError,IndexError,AssertionError,StopIteration):return None
@lru_cache(maxsize=64)
def inputs(seed):
 candidates={'train':[],'test':[]};seen=set();reject=[]
 for attempt in range(24):
  for bi,b in enumerate(CONFIG['banks']):
   try:ep=BANKS[bi].generate(seed+attempt*100003,b['config']['default'],6,4)
   except (ValueError,TypeError,KeyError,IndexError,AssertionError,RuntimeError)as e:reject.append(dict(bank=b['name'],error=str(e)));continue
   for split in ('train','test'):
    for p in ep[split]:
     g=p['input'];k=(bi,json.dumps(g))
     if k in seen:continue
     seen.add(k);ys=table(g)
     if ys is None:reject.append(dict(bank=b['name'],split=split,error='outside current decoder domain'));continue
     candidates[split].append((g,ys,bi))
  tr=[x for x in candidates['train']if x[2]==0][:2]
  if len(tr)<2:continue
  rest=[x for x in candidates['train']if x not in tr]
  if not rest:continue
  if TASK in ('8e5c0c38','dbff022c'):
   import itertools
   rp=BASE/'seventh-rivals.py';rn='_teach_'+hashlib.sha256(str(rp).encode()).hexdigest()
   if rn not in sys.modules:
    rs=importlib.util.spec_from_file_location(rn,rp);rm=importlib.util.module_from_spec(rs);sys.modules[rn]=rm;rs.loader.exec_module(rm)
   rm=sys.modules[rn];pool=candidates['train'];covers=[]
   for x in pool:
    cov=set()
    for mi,mode in enumerate(CONFIG['modes']):
     for name,answer in rm.predictions(__import__('types').SimpleNamespace(**globals()),x[0],mode).items():
      if answer!=x[1][mi]:cov.add((mode,name))
     for mj in range(mi):
      if x[1][mi]!=x[1][mj]:cov.add(('active',mi,mj))
    covers.append(cov)
   universe=set().union(*covers);chosen=None
   preferred=[(0,1,i)for i in range(2,len(pool))]
   for combo in itertools.chain(preferred,itertools.combinations(range(len(pool)),3)):
    if set().union(*(covers[i]for i in combo))==universe:chosen=combo;break
   if chosen is None:continue
   tr=[pool[i]for i in chosen]
  else:tr.append(rest[0])
  if any(all(x[1][i]==x[1][j]for x in tr)for i in range(len(CONFIG['modes']))for j in range(i)):continue
  tr +=[x for x in rest if json.dumps(x[0])not in {json.dumps(y[0])for y in tr}][:6-len(tr)]
  bank=seed%len(CONFIG['banks']);te=[x for x in candidates['test']if x[2]==bank and x[0]not in [z[0]for z in tr]][:4]
  if len(te)<4:continue
  if len(tr)==6:return tr,te,reject
 raise ValueError('current-domain constructor or teaching exhausted')
def generate(seed,settings,demos=3,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**63-1),(demos,MIN_DEMOS,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:seventh-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings),query_source_indices=order[:queries])
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))

def public_bytes(episode,query_index=0):
 return (json.dumps(public_view(episode,query_index),sort_keys=True,separators=(',',':'))+'\n').encode()
