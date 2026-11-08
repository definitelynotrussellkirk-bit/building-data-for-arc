"""Matched episode rules; bank copies preserve exact programs and source provenance."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'union-config.json').read_text());TASK=CONFIG['task'];BANKS={}
for home in sorted((BASE/'banks').iterdir()):
 p=home/'workspace/parametric/adapter.py';name='_bank_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);BANKS[home.name]=m

def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['parameter']}or type(settings[CONFIG['parameter']])is not str or settings[CONFIG['parameter']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return settings[CONFIG['parameter']]

def program(settings):
 mode=selected(settings)
 if TASK=='1818057f':
  if mode=='dominant_component':return BANKS['dominant'].program({'mark_scope':mode})
  if mode=='largest_overlap':return BANKS['overlap'].program({'selection':mode})
  return BANKS['current'].program({'selection':mode})
 if TASK=='195c6913':return BANKS['phase'].program({'phase':'restart'})if mode=='restart'else BANKS['current'].program({'turn':mode})
 return BANKS['current'].program({'stencil_mode':mode})

def predict(g,mode):
 if TASK=='1818057f':
  if mode=='dominant_component':return BANKS['dominant'].impl.solve(g,mode)
  if mode=='largest_overlap':return BANKS['overlap'].engine.solve(g,mode)
  return BANKS['current'].G.solve(g,mode)
 if TASK=='195c6913':return BANKS['phase'].core.solve(g,'restart')if mode=='restart'else BANKS['current'].G.solve(g,mode)
 return BANKS['repaired'].impl.solve(g,mode)

def bank_episode(name,seed):
 settings={'1818057f':{'current':{'selection':'all'},'dominant':{'mark_scope':'all'},'overlap':{'selection':'all'}},'195c6913':{'current':{'turn':'north'},'phase':{'phase':'carry'}},'58f5dbd5':{'current':{'stencil_mode':'cutout'},'repaired':{'stencil_mode':'cutout'},'variable':{'ink_mode':'carve'}}}[TASK][name]
 return BANKS[name].generate(seed,settings,6,4)

@lru_cache(maxsize=64)
def inputs(seed):
 names=list(BANKS);candidates={'train':[],'test':[]};seen=set();reject=[]
 for attempt in range(24):
  for bank in names:
   ep=bank_episode(bank,seed+attempt*100003)
   for split in ('train','test'):
    for p in ep[split]:
     g=p['input'];key=json.dumps(g)
     if key in seen:continue
     seen.add(key)
     try:ys=[predict(g,mode)for mode in CONFIG['modes']]
     except (ValueError,TypeError,KeyError,IndexError,AssertionError)as e:reject.append(dict(bank=bank,split=split,error=str(e)));continue
     candidates[split].append((g,ys,bank))
  # Preserve the repaired fixed-stencil two-demo curriculum; its query bank stays independent.
  if TASK=='58f5dbd5':tr=[x for x in candidates['train']if x[2]=='repaired'][:6]
  else:
   remaining={(i,j)for i in range(len(CONFIG['modes']))for j in range(i)};tr=[];used=set()
   for _ in range(2):
    scores=[sum(ys[i]!=ys[j]for i,j in remaining)if n not in used else-1 for n,(g,ys,b)in enumerate(candidates['train'])]
    if not scores:break
    n=max(range(len(scores)),key=lambda n:(scores[n],candidates['train'][n][2]not in {x[2]for x in tr}));used.add(n);tr.append(candidates['train'][n]);ys=tr[-1][1];remaining={p for p in remaining if ys[p[0]]==ys[p[1]]}
   if remaining:continue
   tr += [x for n,x in enumerate(candidates['train'])if n not in used][:4]
  bank=names[seed%len(names)];te=[x for x in candidates['test']if x[2]==bank][:4]
  if len(tr)==6 and len(te)==4:return tr,te,reject
 raise ValueError('teaching/bank availability exhausted')

def generate(seed,settings,demos,queries):
 mode=selected(settings);index=CONFIG['modes'].index(mode)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:private-query-order:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))

def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
