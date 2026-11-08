"""Exact incumbent rules plus complementary constructors; private query prefixes."""
from pathlib import Path
import copy,json,hashlib,importlib.util,sys,random
from functools import lru_cache
BASE=Path(__file__).resolve().parent;CONFIG=json.loads((BASE/'merge-config.json').read_text());TASK=CONFIG['task'];BANKS=[]
for bank in CONFIG['banks']:
 p=BASE/'banks'/bank['name']/'workspace/parametric/adapter.py';n='_sixth_'+hashlib.sha256(str(p).encode()).hexdigest();sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);BANKS.append(m)
def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['key']}or type(settings[CONFIG['key']])is not str or settings[CONFIG['key']]not in CONFIG['modes']:raise ValueError('one declared setting required')
 return CONFIG['modes'].index(settings[CONFIG['key']])
def program(settings):
 i,s=CONFIG['active'][selected(settings)];return BANKS[i].program(s)
def predict(i,g,s):
 m=BANKS[i];v=next(iter(s.values()))
 if TASK=='8e5c0c38':return m.table(g)[m.MODES.index(v)] if i==0 else m.engine.solve(g,v)
 if TASK=='9bbf930d':return m.CORE.solve(g,v)if i==0 else m.family.solve(g,v)
 if TASK=='a25697e4':return m._native.solve(g,v)if i==0 else m.model.solve(g,v)
 if TASK=='abc82100':return m.family.solve(g,v)if i==0 else m.predict(g,v)if i==1 else m.model.solve(g,v)
 if TASK=='b6f77b65':return m._model.solve(g,either=v=='either_post')if i<2 else m.family.solve(g,s)
def table(g):
 try:return [predict(i,g,s)for i,s in CONFIG['active']]
 except (ValueError,TypeError,KeyError,IndexError,AssertionError,StopIteration):return None
@lru_cache(maxsize=64)
def inputs(seed):
 names=CONFIG['banks'];candidates={'train':[],'test':[]};seen=set();reject=[]
 for attempt in range(24):
  for bi,b in enumerate(names):
   try:ep=BANKS[bi].generate(seed+attempt*100003,b['config']['default'],6,4)
   except (ValueError,TypeError,KeyError,IndexError,AssertionError,RuntimeError)as e:reject.append(dict(bank=b['name'],error=str(e)));continue
   for split in ('train','test'):
    for p in ep[split]:
     g=p['input'];k=(bi,json.dumps(g))
     if k in seen:continue
     seen.add(k);ys=table(g)
     if ys is None:reject.append(dict(bank=b['name'],split=split,error='outside joint rule domain'));continue
     candidates[split].append((g,ys,bi))
  # Retain incumbent teaching prefix; new rule distinctions use demonstration-only candidates.
  tr=[x for x in candidates['train']if x[2]==(1 if TASK=='b6f77b65'else 0)][:3 if TASK=='a25697e4'else 2]
  if len(tr)<2:continue
  rem={(i,j)for i in range(len(CONFIG['modes']))for j in range(i)if all(x[1][i]==x[1][j]for x in tr)}
  rest=[x for x in candidates['train']if x not in tr]
  if not rest:continue
  def score(x):
   points=sum(x[1][i]!=x[1][j]for i,j in rem)
   if TASK=='8e5c0c38':
    mi=CONFIG['modes'].index('horizontal');rivals=[BANKS[1].engine.rivals(z[0],'horizontal')for z in tr]
    surviving=[n for n in rivals[0]if all(r[n]==z[1][mi]for r,z in zip(rivals,tr))]
    rivals_x=BANKS[1].engine.rivals(x[0],'horizontal');points+=sum(rivals_x[n]!=x[1][mi]for n in surviving)
   if TASK=='abc82100':
    mi=CONFIG['modes'].index('quarter_turn');model=BANKS[2].model
    for n in ('only_first_seed','box','zero_anchor','keep_seeds','reverse_mapping'):
     if all(model.apply(z[0],model.extract(z[0]),'quarter_turn',**{n:True})==z[1][mi]for z in tr):points+=model.apply(x[0],model.extract(x[0]),'quarter_turn',**{n:True})!=x[1][mi]
   return points
  best=max(rest,key=score);
  if len(tr)<3:tr.append(best)
  if any(all(x[1][i]==x[1][j]for x in tr)for i,j in rem):continue
  tr +=[x for x in rest if json.dumps(x[0])not in {json.dumps(y[0])for y in tr}][:6-len(tr)]
  # Query constructor selection is independent of setting and query labels.
  bank=seed%len(names);te=[x for x in candidates['test']if x[2]==bank][:4]
  if len(te)<4:continue
  if len(tr)==6:return tr,te,reject
 raise ValueError('joint domain or teaching exhausted')
def generate(seed,settings,demos,queries):
 index=selected(settings)
 for v,lo,hi in ((seed,0,2**63-1),(demos,3,6),(queries,1,4)):
  if type(v)is not int or not lo<=v<=hi:raise ValueError('unsupported integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'{TASK}:query:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][index]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[i])for i in order[:queries]],program_solution=program(settings))
def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))
