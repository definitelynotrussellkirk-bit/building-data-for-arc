"""Exact incumbent programs and broad samplers with source-bound semantic ports."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_eleventh_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
def __getattr__(name):return getattr(BANKS[0],name)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 idx=selected(settings);m=BANKS[0]
 if idx<2:return m.program(settings)
 source=m.program(CONFIG['banks'][0]['config']['default'])
 if TASK=='332f06d7':return source.replace('(define cleared (recolor-cells g zeros 1))','''(define cleared (for*/fold ([out (recolor-cells g zeros 1)]) ([p route] [a (range sh)] [b (range sw)])
       (define r (+ (first p) a)) (define c (+ (second p) b))
       (if (= (at out r c) 1) (set-cell out r c 9) out)))''')
 if TASK=='3dc255db':return source.replace('(in-range 1 (+ payload-count 1))','(in-range 1 (+ (max h w) 1))')
 if TASK=='4c3d4a41':
  source=m.program({CONFIG['key']:'longest_survivor'});return source.replace('(recolor-cells intermediate (pick-max groups length) 1)','''(let ([winner (pick-max groups length)])
     (for/fold ([out intermediate]) ([group groups] #:unless (equal? group winner)) (recolor-cells out group 0)))''')
 if TASK=='58490d8a':return source.replace('(else (length matches))','(else (if (null? matches) 0 (count-if (lambda (o) (= (obj-size o) (apply max (map obj-size matches)))) matches)))')
 if TASK=='62593bfd':
  lam=source[source.index('(lambda (g)'):].strip()[:-1]
  return '''(rule! (lambda (g) (let* ([base '''+lam+'''] [out (base g)] [bg (mode g -1)] [cs (filter (lambda (c) (not (= (at out 0 c) bg))) (range (cols g)))])
   (if (null? cs) out (for/fold ([a out]) ([c (range (apply min cs) (+ 1 (apply max cs)))])
      (if (= (at a 0 c) bg) (set-cell a 0 c (if (= bg 9) 0 9)) a))))))'''
 raise ValueError('unknown extension')
def predict(g,index):
 m=BANKS[0];mode=CONFIG['modes'][index]
 if TASK=='332f06d7':
  if index<2:return m.model.solve(g,mode)
  d=m.model.analyze(g);out=m.model.solve(g);sh,sw=d['shape']
  for r,c in d['route']:
   for a in range(sh):
    for b in range(sw):
     if out[r+a][c+b]==1:out[r+a][c+b]=9
  return out
 if TASK=='3dc255db':
  if index<2:return m.solve(g,mode)
  ships=m.descriptors(g);out=copy.deepcopy(g)
  for s in ships:
   for r,c in s['payload_cells']:out[r][c]=0
  for s in ships:
   r,c=s['tip'];dr,dc=s['vector'];r+=dr;c+=dc
   while 0<=r<len(g)and 0<=c<len(g[0]):out[r][c]=s['payload_color'];r+=dr;c+=dc
  return out
 if TASK=='4c3d4a41':
  if index<2:return m.solve(g,mode)
  d=m.extract(g);out=m.insertion(g,d);groups=m.surviving(out,d);winner=max(groups,key=len)
  for group in groups:
   if group!=winner:
    for r,c in group:out[r][c]=0
  return out
 if TASK=='58490d8a':
  if index<2:return m.predict(g,mode)
  d=m.analyze(g);out=[[0]*d['width']for _ in range(d['height'])]
  for e in d['entries']:
   parts=[p for p in d['components']if g[p[0][0]][p[0][1]]==e['color']];maximum=max(map(len,parts),default=0);n=sum(len(p)==maximum for p in parts)
   for c in range(e['column'],min(d['width'],e['column']+2*n),2):out[e['row']][c]=e['color']
  return out
 if TASK=='62593bfd':
  if index<2:return m.model.solve(g,mode)
  out=m.model.solve(g);bg=m.model.analyze(g)['background'];cs=[c for c,v in enumerate(out[0])if v!=bg]
  if cs:
   for c in range(min(cs),max(cs)+1):
    if out[0][c]==bg:out[0][c]=0 if bg==9 else 9
  return out
@lru_cache(maxsize=64)
def inputs(seed):
 ep=BANKS[0].generate(seed,CONFIG['banks'][0]['config']['default'],6,4)
 pack=lambda p,b:(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 tr=[pack(p,0)for p in ep['train']];te=[pack(p,0)for p in ep['test']];rejected=[]
 bank=seed%len(BANKS)
 if bank:
  b=CONFIG['banks'][bank]
  try:
   other=BANKS[bank].generate(seed,b['config']['default'],6,4);new=[];seen={json.dumps(x[0])for x in tr}
   for p in other['test']:
    try:
     x=pack(p,bank);key=json.dumps(x[0])
     if key in seen:rejected.append(dict(bank=b['name'],kind='duplicate_input',error='matches demonstration or earlier query'));continue
     seen.add(key);new.append(x)
    except (ValueError,TypeError,IndexError,KeyError,AssertionError,StopIteration)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_domain'))
   if new:te=(new+[x for x in te if json.dumps(x[0])not in seen])[:4]
  except (ValueError,TypeError,IndexError,KeyError,AssertionError,RuntimeError)as e:rejected.append(dict(bank=b['name'],error=str(e),kind='incoming_sampler'))
 def rejects_shortcuts(i,j):
  if TASK!='3dc255db':return True
  for a in range(len(CONFIG['modes'])):
   for name in BANKS[0].RIVALS:
    ys=[BANKS[0].rival(v[0],name)for v in tr+te]
    if any(y!=v[1][a]for y,v in zip(ys,tr+te)) and all(ys[k]==tr[k][1][a]for k in(i,j)):return False
  return True
 for i,j in itertools.combinations(range(len(tr)),2):
  if rejects_shortcuts(i,j) and all(any(tr[k][1][a]!=tr[k][1][b]for k in(i,j))for a in range(len(CONFIG['modes']))for b in range(a)):
   tr=[tr[i],tr[j]]+[v for k,v in enumerate(tr)if k not in(i,j)];break
 else:raise ValueError('six current lessons lack distinguishing two-demo prefix')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**256 if TASK=='58490d8a'else 2**63-1),(demos,2,6),(queries,4 if TASK=='62593bfd'else 1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:eleventh-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
