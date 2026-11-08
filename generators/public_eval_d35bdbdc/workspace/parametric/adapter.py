"""Exact accepted programs and source-local complementary sampler/rule banks."""
from pathlib import Path
import importlib.util,hashlib,sys,json,copy,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'union-config.json').read_text());TASK=CONFIG['task']
def load(rel):
 p=BASE/rel;n='_union17_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
if TASK in ('d35bdbdc','dd6b8c4b'):
 C=load('banks/current/workspace/parametric/adapter.py');N=load('banks/extra/workspace/parametric/adapter.py')
else:C=load('incumbent.py')
if TASK=='d59b0160':N=load('banks/new/workspace/parametric/adapter.py')
if TASK=='dbff022c':R=load('seventh-rivals.py')
def selected(s):
 if type(s)is not dict or set(s)!={CONFIG['key']}or type(s[CONFIG['key']])is not str or s[CONFIG['key']]not in CONFIG['modes']:raise ValueError('exact declared setting required')
 return s[CONFIG['key']]
def program(s):
 mode=selected(s)
 if mode in CONFIG['old']:return C.program(s)
 if TASK=='dd6b8c4b':return N.program(s)
 source=C.program(CONFIG['default']);anchor='   (for/fold ((out stage-one)) ((o survivors) #:when (= (obj-size o) area))\n    (recolor-cells out (obj-cells o) bg))'
 if source.count(anchor)!=1:raise ValueError('incumbent completion anchor changed')
 if mode=='largest_survivor':body='''   (if (null? survivors) stage-one
     (for/fold ((out stage-one)) ((p (obj-cells (pick-max survivors obj-size))))
       (if (= (at out (first p) (second p)) 0) (set-cell out (first p) (second p) 3) out)))'''
 elif mode=='highlight_closest_survivor':body='''   (define (missing o) (count-if (lambda (v) (not (member v (palette o)))) key-colors))
   (define least-missing (if (null? survivors) -1 (apply min (map missing survivors))))
   (for/fold ((out stage-one)) ((o survivors) #:when (= (missing o) least-missing))
    (for/fold ((a out)) ((p (obj-cells o)) #:when (not (= (at a (first p) (second p)) 0)))
     (set-cell a (first p) (second p) 9)))'''
 else:body='''   (define (extras o) (filter (lambda (v) (not (member v key-colors))) (palette o)))
   (define selected-panels
    (for/fold ((selected matches)) ((i (range (length panels))))
     (define active (remove-duplicates (apply append (map extras selected))))
     (filter (lambda (o) (or (member o selected) (for/or ((v (extras o))) (member v active)))) panels)))
   (for/fold ((out g)) ((o selected-panels)) (recolor-cells out (obj-cells o) bg))'''
 return source.replace(anchor,body)
def predict(g,mode):
 if TASK=='d35bdbdc':return N.predict(g,mode)
 if TASK=='dd6b8c4b':return N.solve(g,mode)
 if TASK=='dbff022c':return C.table(g)[CONFIG['modes'].index(mode)]
 if mode in CONFIG['old']:return C.predict(g,CONFIG['old'].index(mode))
 d=C.BANKS[0].analyze(g);out=C.BANKS[0].predict(g);ps=d['panels'];surv=[p for p in ps if not p['matched']]
 if mode=='largest_survivor':
  if surv:
   for r,c in max(surv,key=lambda p:len(p['cells']))['cells']:
    if out[r][c]==0:out[r][c]=3
 elif mode=='highlight_closest_survivor':
  missing=lambda p:len(set(d['key_colors'])-set(p['colors']));minimum=min(map(missing,surv),default=-1)
  for p in surv:
   if missing(p)==minimum:
    for r,c in p['cells']:
     if out[r][c]!=0:out[r][c]=9
 else:
  selected=[p for p in ps if p['matched']]
  for _ in ps:
   active=set().union(*(set(p['colors'])-set(d['key_colors'])for p in selected))if selected else set()
   selected=[p for p in ps if p in selected or(set(p['colors'])-set(d['key_colors']))&active]
  for p in selected:
   for r,c in p['cells']:out[r][c]=7
 return out
def rivals(g,mode):
 if TASK=='d35bdbdc':return {n:N.predict(g,n)for n in N.rivals()if n!=mode}
 if TASK=='dd6b8c4b':return {n:N.solve(g,mode,rival=n)for n in N.RIVALS}
 if TASK=='dbff022c':return R.predictions(C,g,mode)
 out={n:C.BANKS[0].predict(g,n)for n in C.BANKS[0].RIVALS if n!=mode}
 d=C.BANKS[0].analyze(g);surv=[p for p in d['panels']if not p['matched']]
 if mode=='largest_survivor':
  for name,ps in [('source_rank',d['panels']),('smallest',sorted(surv,key=lambda p:-len(p['cells']))),('first',surv),('last',surv[::-1])]:
   y=C.BANKS[0].predict(g)
   p=(max(ps,key=lambda p:len(p['cells']))if name=='source_rank'else min(ps,key=lambda p:len(p['cells']))if name=='smallest'else ps[0])if ps else None
   if p:
    for r,c in p['cells']:
     if y[r][c]==0:y[r][c]=3
   out[name]=y
  out['no_finish']=C.BANKS[0].predict(g)
 if mode=='highlight_closest_survivor':
  for name,ps in [('source_rank',d['panels']),('furthest',surv)]:
   y=C.BANKS[0].predict(g);missing=lambda p:len(set(d['key_colors'])-set(p['colors']));score=(min if name=='source_rank'else max)(map(missing,ps),default=-1)
   for p in ps:
    if missing(p)==score:
     for r,c in p['cells']:
      if y[r][c]not in(0,7):y[r][c]=9
   out[name]=y
 if mode=='palette_cascade':
  ps=d['panels'];keys=set(d['key_colors']);seed=[p for p in ps if p['matched']]
  for name,act in [('global_palette',set().union(*(set(p['colors'])-keys for p in ps))),('include_keys',set().union(*(set(p['colors'])for p in seed))if seed else set()),('one_wave',set().union(*(set(p['colors'])-keys for p in seed))if seed else set())]:
   y=copy.deepcopy(g)
   for p in ps:
    if p in seed or (set(p['colors']) if name=='include_keys'else set(p['colors'])-keys)&act:
     for r,c in p['cells']:y[r][c]=7
   out[name]=y
 return out
@lru_cache(maxsize=64)
def inputs(seed):
 pools=[];seen=set();querybanks=[];rejected=[]
 def add(ep,bank):
  tr=[];te=[]
  for split,target in [('train',tr),('test',te)]:
   for p in ep[split]:
    g=p['input'];token=json.dumps(g)
    try:ys=[predict(g,m)for m in CONFIG['modes']]
    except (ValueError,IndexError,KeyError,TypeError,AssertionError,StopIteration)as e:rejected.append(dict(bank=bank,reason=str(e)));continue
    if any(y is None for y in ys):continue
    target.append((g,ys,bank))
  for x in tr:
   k=json.dumps(x[0])
   if k not in seen:pools.append(x);seen.add(k)
  if len(te)==4:querybanks.append(te)
 if TASK in ('d35bdbdc','dd6b8c4b'):
  add(C.generate(seed,CONFIG['default'],6,4),'current');add(N.generate(seed,CONFIG['default'],6,4),'extra')
 elif TASK=='d59b0160':
  add(C.generate(seed,CONFIG['default'],6,4),'current')
  for i,b in enumerate(C.BANKS):add(b.generate(seed,C.CONFIG['banks'][i]['config']['default'],6,4),'prior'+str(i))
  add(N.generate(seed,{'finish':'erase'},6,4),'new')
 else:
  add(C.generate(seed,CONFIG['default'],6,4),'current')
  for i,b in enumerate(C.BANKS):add(b.generate(seed,C.CONFIG['banks'][i]['config']['default'],6,4),'prior'+str(i))
 # Use every compatible sampler, independently of setting; preserve each bank's
 # four queries and its 30x30 case. The two visible lessons must separate all
 # declared settings and every finite rival distinguishable in the lesson pool.
 covers=[]
 for g,ys,bank in pools:
  c=set()
  for i,m in enumerate(CONFIG['modes']):
   for n,y in rivals(g,m).items():
    if y!=ys[i]:c.add((m,n))
   for j in range(i):
    if ys[i]!=ys[j]:c.add(('setting',i,j))
  covers.append(c)
 universe=set().union(*covers);pair=next(((i,j)for i,j in itertools.combinations(range(len(pools)),2)if covers[i]|covers[j]==universe),None)
 if pair is None:raise ValueError('no two-demo finite-rival separating curriculum')
 order=list(pair)+[i for i in range(len(pools))if i not in pair];tr=[pools[i]for i in order[:6]]
 bank=seed%len(querybanks);te=querybanks[bank]
 if len(tr)!=6 or len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('ten distinct inputs required')
 return tr,te,rejected
def generate(seed,s,demos=2,queries=4):
 mode=selected(s)
 # Ordinary public d59 generator hashes user seeds into a wider integer domain.
 if TASK=='d59b0160'and type(seed)is int and seed>2**63-1:return C.generate(seed,s,demos,queries)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported exact integer')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'union17:{TASK}:{seed}').shuffle(order);i=CONFIG['modes'].index(mode)
 def pair(x):return dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][i]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[j])for j in order[:queries]],program_solution=program(s))
def public_view(ep,index=0):
 if type(index)is not int or not 0<=index<len(ep['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in ep['train']],test=[dict(input=ep['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
