"""Preserved active rules and source-local compatible constructor union."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_tenth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 idx=selected(settings)
 if idx<2:return BANKS[0].program(settings)
 source=BANKS[0].program(CONFIG['banks'][0]['config']['default'])
 assert TASK=='16de56c4'
 return source.replace('(define continue-after-hit #f)','(define continue-after-hit #t)',1).replace('(ink (if hit (list-ref values hit) seed-color))','(ink seed-color)',1)
def predict(g,index):
 m=BANKS[0];mode=CONFIG['modes'][index]
 if TASK=='13e47133':return m.CORE.solve(g,mode)
 if TASK=='16de56c4':
  if index<2:return m.engine.solve(g,mode)
  plan=m.engine.analyze(g);out=copy.deepcopy(g);h,w=len(g),len(g[0])
  for ray in plan['rays']:
   for t in range(0,plan['length'],ray['spacing']):
    r,c=m.engine.coordinate(plan['side'],ray['line'],t,h,w);out[r][c]=ray['color']
  return out
 if TASK=='20270e3b':return m._source.solve(g,mode)
 if TASK=='2c181942':return m.G.solve(g,mode)
 if TASK=='31f7f899':return m._native.solve(g,mode)
 raise ValueError(TASK)
@lru_cache(maxsize=64)
def inputs(seed):
 ep=BANKS[0].generate(seed,CONFIG['banks'][0]['config']['default'],6,4)
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
 for i,j in itertools.combinations(range(len(tr)),2):
  if all(any(tr[k][1][a]!=tr[k][1][b]for k in (i,j))for a in range(len(CONFIG['modes']))for b in range(a)):
   tr=[tr[i],tr[j]]+[v for k,v in enumerate(tr)if k not in (i,j)];break
 else:raise ValueError('six lessons lack distinguishing two-demo prefix')
 return tr,te,rejected
def generate(seed,settings,demos=2,queries=4):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,CONFIG['banks'][0]['config']['limits']['queries'][0],4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:tenth-query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
