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
 return source_only_routing_bank(seed) if TASK=='195c6913' and name=='current' else BANKS[name].generate(seed,settings,6,4)

@lru_cache(maxsize=64)
def inputs(seed):
 names=list(BANKS);candidates={'train':[],'test':[]};seen=set();reject=[]
 for attempt in range(8):
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
   finite={(i,j)for i in range(len(CONFIG['modes']))for j in range(i)}
   rivaltables=[rival_table(x[0]) for x in candidates['train']]
   rivalkeys=set(rivaltables[0]) if rivaltables else set()
   remaining={('finite',i,j)for i,j in finite}|{('rival',mode,n)for mode,n in rivalkeys};tr=[];used=set()
   covers=[]
   for (g,ys,bank),rivals in zip(candidates['train'],rivaltables):
    covers.append({('finite',i,j)for i,j in finite if ys[i]!=ys[j]}|{('rival',mode,n)for (mode,n),y in rivals.items()if ys[CONFIG['modes'].index(mode)]!=y})
   for _ in range(3):
    scores=[len(cover&remaining)if n not in used else-1 for n,cover in enumerate(covers)]
    if not scores:break
    n=max(range(len(scores)),key=lambda n:(scores[n],candidates['train'][n][2]not in {x[2]for x in tr}));used.add(n);tr.append(candidates['train'][n]);remaining-=covers[n]
   if remaining:continue
   tr += [x for n,x in enumerate(candidates['train'])if n not in used][:6-len(tr)]
  bank=names[seed%len(names)];te=[x for x in candidates['test']if x[2]==bank][:4]
  if len(tr)==6 and len(te)==4:return tr,te,reject
 raise ValueError('teaching/bank availability exhausted')

def generate(seed,settings,demos,queries):
 mode=selected(settings);index=CONFIG['modes'].index(mode)
 for v,lo,hi in ((seed,0,2**63-1),(demos,3,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:private-query-order:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))

def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))


def rival_table(g):
 result={}
 if TASK=='1818057f':
  a=BANKS['current'].G
  for mode in ('all','largest'):
   for n in a.RIVALS:
    if n in ({'all_crosses','eight_connected'}if mode=='all'else{'largest_cross_component'}):continue
    result[(mode,'current/'+n)]=a.solve(g,mode,n)
  a=BANKS['overlap'].engine
  for n,y in a.rivals(g,'largest_overlap').items():
   if n!='largest_overlap':result[('largest_overlap','overlap/'+n)]=y
  a=BANKS['dominant'].impl
  for n in ('exact_only','first_center','last_center','one_per_component','first_component','last_component','largest_area','smallest_area','topmost_centers','paint_components','all_fours'):
   result[('dominant_component','dominant/'+n)]=a.rival_solve(g,'dominant_component',n)
 elif TASK=='195c6913':
  a=BANKS['current'].G
  for mode in ('north','south'):
   for n in a.RIVALS:result[(mode,'current/'+n)]=a.solve(g,mode,rival=n)
  a=BANKS['phase']
  for n in a.RIVALS:result[('restart','phase/'+n)]=a.core.solve(g,'restart',rival=n)
 return result

def source_only_routing_bank(seed):
 a=BANKS['current'].G;grids=[]
 for slot in range(10):
  for attempt in range(128):
   g=a.scene(seed,slot,attempt,stress=slot==9);facts=a.parse(g);lawful=True
   for turn in ('north','south'):
    used=set()
    for start in facts['starts']:
     path,bumps=a.trace(g,start,road=facts['road'],wall=facts['wall'],turn=turn);pts=set(path+bumps)
     if used&pts or len(bumps)<1:lawful=False
     used.update(pts)
   if lawful:break
  else:raise ValueError('routing geometry generation exhausted')
  grids.append(g)
 return dict(train=[dict(input=g)for g in grids[:6]],test=[dict(input=g)for g in grids[6:]])
