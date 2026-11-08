"""Exact incumbent rules, semantic ports and compatible incoming input banks."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_ninth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
def __getattr__(name):return getattr(BANKS[0],name)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 idx=selected(settings);mode=CONFIG['modes'][idx];m=BANKS[0]
 if idx<2:return m.program(settings)
 source=m.program(CONFIG['banks'][0]['config']['default'])
 if TASK=='65b59efc':
  if mode=='transpose_layout':return source.replace('(+ (* r n) rr) (+ (* c n) cc)','(+ (* c n) rr) (+ (* r n) cc)')
  insertion="""   (define occupied (for*/list ([r (in-range n)] [c (in-range n)] #:when (not (= (at layout r c) 0))) (list r c (at layout r c))))
   (define maximum-frequency (apply max (map (lambda (p) (count-if (lambda (q) (= (third p) (third q))) occupied)) occupied)))
   (define effective-layout (for/fold ([out layout]) ([p occupied] [i (in-naturals)])
     (set-cell out (first p) (second p) VALUE)))
"""
  value='(third (list-ref occupied (modulo (+ i 1) (length occupied))))' if mode=='next_token' else '(if (= (count-if (lambda (q) (= (third p) (third q))) occupied) maximum-frequency) (third p) 0)'
  source=source.replace('   (for*/fold ((out (build-grid',insertion.replace('VALUE',value)+'   (for*/fold ((out (build-grid')
  source=source.replace('#:when (not (= (at layout r c) 0)))\n    (let*', '#:when (not (= (at effective-layout r c) 0)))\n    (let*').replace('(= (first t) (at layout r c))','(= (first t) (at effective-layout r c))')
  return source
 if TASK=='d59b0160':return source.replace('(define output-policy "all_matches")',f'(define output-policy "{mode}")',1)
 if TASK=='db0c5428':return m.program({CONFIG['key']:'rarest_tip'}).replace('(apply min (map frequency','(apply max (map frequency')
 if TASK=='da515329':
  lam=source[source.index('(lambda (g)'):].strip()[:-1]
  return '(rule! (lambda (g) (let ([base '+lam+''']) (let* ([completed (base g)] [groups (objects completed 0)] [selected (pick-max groups obj-size)]) (for/fold ([out completed]) ([p (obj-cells selected)]) (set-cell out (first p) (second p) 2))))))'''
 if TASK=='b99e7126':
  source=source.replace('   (define paints','   (define dense-row (pick-max (sort (remove-duplicates (map first selected-mask)) <) (lambda (r) (count-if (lambda (p) (= (first p) r)) selected-mask))))\n   (define paints')
  return source.replace('(at anomaly r c)))))))','(if (and (= (first p) dense-row) (= (at anomaly r c) ink)) 9 (at anomaly r c))))))))')
 raise ValueError('unknown extension')
def predict(g,index):
 m=BANKS[0];mode=CONFIG['modes'][index]
 if TASK=='65b59efc':
  if index<2:return m.P.solve(g,mode)
  d=m.P.analyse(g)
  if mode=='transpose_layout':return m.P.render(d,'as_drawn','transpose_layout')
  occupied=[(r,c,v)for r,row in enumerate(d['layout'])for c,v in enumerate(row)if v]
  maximum=max(sum(v==p[2]for p in occupied)for r,c,v in occupied)
  for i,(r,c,v) in enumerate(occupied):d['layout'][r][c]=occupied[(i+1)%len(occupied)][2] if mode=='next_token' else v if sum(v==p[2]for p in occupied)==maximum else 0
  return m.P.render(d)
 if TASK=='d59b0160':return m.predict(g,mode)
 if TASK=='db0c5428':return m.CORE.solve(g,'all',rival=mode)if index==2 else m.CORE.solve(g,mode)
 if TASK=='da515329':
  if index<2:return m.engine.solve(g,mode)
  out=m.engine.solve(g,'clockwise');cells={(r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v};groups=[]
  while cells:
   p=min(cells);cells.remove(p);stack=[p];grp=[]
   while stack:
    r,c=stack.pop();grp.append((r,c))
    for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
     if q in cells:cells.remove(q);stack.append(q)
   groups.append(grp)
  for r,c in max(groups,key=len):out[r][c]=2
  return out
 if TASK=='b99e7126':
  if index<2:return m.G.solve(g,mode)
  d=m.G.analyze(g);out=m.G.solve(g,'all_ink');row=min({r for r,c in d['mask']},key=lambda r:(-sum(rr==r for rr,cc in d['mask']),r));ar,ac=d['anchor']
  for r,c in d['mask']:
   if r!=row:continue
   r0=d['row_bands'][ar+r][0];c0=d['col_bands'][ac+c][0]
   for rr,cc in d['mask']:out[r0+rr][c0+cc]=9
  return out
@lru_cache(maxsize=64)
def inputs(seed):
 ep=BANKS[0].generate(seed,CONFIG['banks'][0]['config']['default'],6,4)
 pack=lambda p,b:(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 tr=[pack(p,0)for p in ep['train']];te=[pack(p,0)for p in ep['test']];rejected=[]
 # Preserve every incumbent demonstration and all constructors. Incoming queries
 # rotate across banks independently of the selected setting.
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
 # Order existing lessons to expose every selected rule in the first two.
 import itertools
 def teaches_extra(i,j):
  if TASK!='db0c5428':return True
  core=BANKS[0].CORE
  for a in range(len(CONFIG['modes'])):
   for rival in core.RIVALS:
    ys=[core.solve(v[0],'all',rival=rival)for v in tr]
    if any(y!=v[1][a]for y,v in zip(ys,tr)) and all(ys[k]==tr[k][1][a]for k in (i,j)):return False
  return True
 for i,j in itertools.combinations(range(len(tr)),2):
  if teaches_extra(i,j) and all(any(tr[k][1][a]!=tr[k][1][b]for k in (i,j))for a in range(len(CONFIG['modes']))for b in range(a)):
   tr=[tr[i],tr[j]]+[v for k,v in enumerate(tr)if k not in (i,j)];break
 else:raise ValueError('incumbent six lessons lack a distinguishing two-demo prefix')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**256 if TASK=='d59b0160' else 2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:ninth-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
