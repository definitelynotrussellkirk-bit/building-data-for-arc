"""Exact retained rules on matched episode inputs; constructor and presentation independent of setting."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'union-config.json').read_text());TASK=CONFIG['task'];BANKS={}
for bank in ('current','extra'):
 p=BASE/'banks'/bank/'workspace/parametric/adapter.py';name='_bank_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);BANKS[bank]=m
C=BANKS['current'];X=BANKS['extra']
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['parameter']}or type(settings[CONFIG['parameter']])is not str or settings[CONFIG['parameter']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return settings[CONFIG['parameter']]
def program(settings):
 m=selected(settings)
 if m in CONFIG['modes'][:2]:return C.program(settings)
 return X.program({{'6e453dd6':'signal_policy','71e489b6':'selection','7b5033c1':'finish','88e364bc':'motion_extent'}[TASK]:m})
def predict(g,m):
 if TASK=='6e453dd6':return X.predict(g,m)if m=='largest_exposed'else C.CORE.solve(g,m)
 if TASK=='71e489b6':return X.solve(g,m)
 if TASK=='7b5033c1':return X.family.solve(g,m)if m=='length_addressed_run'else C.G.solve(g,m)
 if TASK=='7b80bb43':return C.family.solve(g,m)
 return X.model.solve(g,m)if m=='halfway'else C.mirror(g,{'motion':m})
def bank_episode(name,seed):
 key=CONFIG['parameter'];default=CONFIG['modes'][0]
 if name=='extra':key,default={'6e453dd6':('signal_policy','all_exposed'),'71e489b6':('selection','all_rims'),'7b5033c1':('finish','unroll'),'7b80bb43':('finish','straighten'),'88e364bc':('motion_extent','to_wall')}[TASK]
 ep=BANKS[name].generate(seed,{key:default},6,4)
 if TASK=='6e453dd6' and name=='extra':
  for split in ('train','test'):
   for p in ep[split]:p['input']=X._normalize(p['input'])[0]
 return ep
@lru_cache(maxsize=64)
def inputs(seed):
 candidates={'train':[],'test':[]};seen=set();reject=[]
 for attempt in range(20):
  for bank in BANKS:
   ep=bank_episode(bank,seed+attempt*100003)
   for split in ('train','test'):
    for p in ep[split]:
     g=p['input'];key=json.dumps(g)
     if key in seen:continue
     seen.add(key)
     try:ys=[predict(g,m)for m in CONFIG['modes']]
     except (ValueError,TypeError,KeyError,IndexError,AssertionError)as e:reject.append(dict(bank=bank,split=split,error=str(e)));continue
     candidates[split].append((g,ys,bank))
  # Keep the incumbent two-demo curriculum, then teach the complementary rule.
  current=[x for x in candidates['train']if x[2]=='current']
  extra=[x for x in candidates['train']if x[2]=='extra']
  tr=current[:2]
  if TASK=='71e489b6':tr+=extra[:1]
  elif TASK=='7b80bb43':tr+=current[2:3]
  else:tr+=extra[:1]
  remaining={(i,j)for i in range(len(CONFIG['modes']))for j in range(i)if all(x[1][i]==x[1][j]for x in tr)}
  if remaining:continue
  tr += [x for x in candidates['train']if x not in tr][:6-len(tr)]
  bank=('current','extra')[seed%2];te=[x for x in candidates['test']if x[2]==bank][:4]
  # Identical constructor banks are deduplicated; preserve their single domain.
  if TASK=='7b80bb43':te=candidates['test'][:4]
  if len(tr)==6 and len(te)==4:return tr,te,reject
 raise ValueError('teaching/bank availability exhausted')
def generate(seed,settings,demos=2,queries=4):
 mode=selected(settings);idx=CONFIG['modes'].index(mode)
 for v,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported exact integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:query-order:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][idx]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index=0):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))

# Preserve the ordinary generator API supplied by its accepted adjacent adapter.
def __getattr__(name):return getattr(C,name)
