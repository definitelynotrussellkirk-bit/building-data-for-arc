"""Exact-program union with setting-independent compatible input banks."""
from pathlib import Path
import importlib.util,sys,hashlib,json,copy,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task']
def load(p):
 n='_merge18_'+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
C=load(BASE/'incumbent.py');BANKS={b['name']:load(BASE/'banks'/b['name']/'adapter.py') for b in CONFIG['banks']}
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']} or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('exact declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 mode=CONFIG['modes'][selected(settings)]
 if mode in CONFIG['oldmodes']:return C.program(settings)
 e=next(x for x in CONFIG['extras']if x['mode']==mode);b=next(x for x in CONFIG['banks']if x['name']==e['bank']);return BANKS[e['bank']].program({next(iter(b['config']['parameters'])):e['source_mode']})
def predict(g,index):
 mode=CONFIG['modes'][index]
 if mode in CONFIG['oldmodes']:
  if TASK.endswith('dfadab01'):return C.P.solve(g,mode)
  if TASK.endswith('e12f9a14'):return C.impl.solve(g,mode)
  if TASK.endswith('e376de54'):return C._native.solve(g,mode)
  return C.model.solve(g,mode)
 e=next(x for x in CONFIG['extras']if x['mode']==mode);m=BANKS[e['bank']]
 if mode=='largest_edit':return m.predict(g,e['source_mode'])
 if mode=='highlight_largest_adjustment':return m.engine.solve(g,e['source_mode'])
 if mode=='primitive_snake':return m.predict(g,e['source_mode'])
 raise ValueError('unknown mode')
def rivals(g):
 out={}
 for i,a in enumerate(CONFIG['modes']):
  for j,b in enumerate(CONFIG['modes']):
   if i!=j:out[a+':setting:'+b]=(predict(g,i),predict(g,j))
 if TASK.endswith('e376de54'):
  m=BANKS['be547a6168f77dde']
  for r in m.RIVALS:out['largest_edit:'+r]=(predict(g,2),m.predict(g,r))
 if TASK.endswith('f931b4a8'):
  m=BANKS['bb9e1eaa903d9afc']
  for r in m._engine.POLICIES:
   if r!='snake':out['primitive_snake:'+r]=(predict(g,2),m.predict(g,r))
 if TASK.endswith('e87109e9'):
  for a in CONFIG['modes']:
   for r in C.model.RIVALS:out[a+':'+r]=(C.model.solve(g,a),C.model.solve(g,a,r))
 if TASK.endswith('e12f9a14'):
  for a in CONFIG['modes']:
   for r in C.impl.RIVALS:
    try:out[a+':'+r]=(C.impl.solve(g,a),C.impl.solve(g,a,rival=r))
    except TypeError:pass
 return out
@lru_cache(maxsize=64)
def inputs(seed):
 current=C.generate(seed,CONFIG['default'],6,4);tr=[];te=[];excluded=[]
 def packed(p,b):return(p['input'],[predict(p['input'],i)for i in range(len(CONFIG['modes']))],b)
 for p in current['train']:tr.append(packed(p,'current'))
 for p in current['test']:te.append(packed(p,'current'))
 if TASK.endswith('e376de54'):
  for offset in (7919,7920):
   ep=C.generate((seed+offset)%(2**63),CONFIG['default'],6,4)
   tr += [packed(p,'current-teaching') for p in ep['train']+ep['test']]
 banks=[]
 for b in CONFIG['banks']:
  m=BANKS[b['name']];ep=m.generate(seed,b['config']['default'],6,4);bt=[];bq=[]
  for split,target in [('train',bt),('test',bq)]:
   for i,p in enumerate(ep[split]):
    try:
     x=packed(p,b['name'])
     if x[1][0]!=p['output']:raise ValueError('incoming default differs from preserved default')
     target.append(x)
    except (ValueError,IndexError,KeyError,AssertionError)as e:excluded.append(dict(bank=b['name'],split=split,index=i,reason=str(e)))
  tr=bt+tr if TASK.endswith('dfadab01') else tr+bt
  if len(bq)==4:banks.append(bq)
 # The entire incumbent query bank remains in rotation, independent of setting.
 te=([te]+banks)[seed%(1+len(banks))]
 seen={json.dumps(x[0])for x in te};unique=[]
 for x in tr:
  k=json.dumps(x[0])
  if k not in seen:unique.append(x);seen.add(k)
 tr=unique;certs=[{k for k,(a,b)in rivals(x[0]).items()if a!=b}for x in tr];need=set().union(*certs,*[{k for k,(a,b)in rivals(x[0]).items()if a!=b} for x in te])
 pairs=[(i,j)for i in range(len(tr))for j in range(i+1,len(tr))if certs[i]|certs[j]==need]
 pair=next(((i,j)for i,j in pairs if all(tr[i][1][a]!=tr[i][1][b]or tr[j][1][a]!=tr[j][1][b]for a in range(len(CONFIG['modes']))for b in range(a))),None)
 if pair is None:raise ValueError('no two-demo teaching cover')
 order=list(pair)+[i for i in range(len(tr))if i not in pair];tr=[tr[i]for i in order[:6]]
 if len(tr)!=6 or len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('ten distinct inputs required')
 return tr,te,excluded
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for x,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(x)is not int or not lo<=x<=hi:raise ValueError('exact integer request outside limits')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:merge18:{seed}').shuffle(order)
 def pair(x):return dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
