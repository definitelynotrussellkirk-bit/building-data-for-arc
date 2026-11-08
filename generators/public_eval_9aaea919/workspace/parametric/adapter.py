"""Disjoint episode constructors with exact retained Racket programs.

Each setting keeps its source constructor; no cross-domain intersection is used.
The full private query bank is shuffled before prefix selection. Only the public
view allowlist is safe to expose. Racket independently verifies all labels and
finite setting identification; Python labels remain generation claims.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,random,sys
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'branch-config.json').read_text())
BANKS={}
for name in {s['bank'] for s in CONFIG['settings']}|({CONFIG['repair_bank']} if 'repair_bank' in CONFIG else set()):
 p=BASE/'banks'/name/'workspace/parametric/adapter.py'
 key='_repeat_branch_'+hashlib.sha256(str(p).encode()).hexdigest()
 sp=importlib.util.spec_from_file_location(key,p);m=importlib.util.module_from_spec(sp);sys.modules[key]=m;sp.loader.exec_module(m);BANKS[name]=m

def selected(settings):
 if type(settings)is not dict or set(settings)!={CONFIG['parameter']}:raise ValueError('one declared setting required')
 for row in CONFIG['settings']:
  if type(settings[CONFIG['parameter']])is str and row['name']==settings[CONFIG['parameter']]:return row
 raise ValueError('undeclared setting')

def program(settings):
 row=selected(settings);return BANKS[row['bank']].program(row['settings'])

def generate(seed,settings,demos,queries):
 row=selected(settings)
 for value,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(value)is not int or not lo<=value<=hi:raise ValueError('unsupported exact integer request')
 bank=CONFIG.get('repair_bank') if 'repair_bank' in CONFIG and seed%2 else row['bank']
 ep=BANKS[bank].generate(seed,copy.deepcopy(row['settings']),6,4)
 order=list(range(4));random.Random(f'repeat-private-order:{seed}').shuffle(order)
 pair=lambda p:dict(input=copy.deepcopy(p['input']),output=copy.deepcopy(p['output']))
 return dict(train=[pair(p) for p in ep['train'][:demos]],test=[pair(ep['test'][i]) for i in order[:queries]],program_solution=program(settings))

def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output']) for p in episode['train']],test=[dict(input=episode['test'][index]['input'])]))

from functools import lru_cache

def predict(g,index):
 row=CONFIG['settings'][index];name=row['name'];a=BANKS['current'];b=BANKS['incoming']
 if CONFIG['parameter']=='aggregation':
  if name in ('balanced','broadcast'):return b.CORE.solve(g,name)
  # Exact mirror of the retained single-first-receiver Racket on multi-receiver scenes.
  f=a.family;os=f.components(g,max(set(v for r in g for v in r),key=lambda v:sum(r.count(v) for r in g)))
  bg=max(set(v for r in g for v in r),key=lambda v:sum(r.count(v) for r in g));my=max(o['r2'] for o in os)
  marks=[o for o in os if o['r1']==o['r2']==my and o['color'] in (2,3)];bodies=[o for o in os if o not in marks]
  stack=lambda m:[o for o in bodies if (o['c1'],o['c2'])==(m['c1'],m['c2'])]
  ds=[stack(m) for m in marks if m['color']==2];rec=stack(next(m for m in marks if m['color']==3));top=min(rec,key=lambda o:o['r1']);bottom=max(rec,key=lambda o:o['r1'])
  st=dict(background=bg,markers=marks,donor_stacks=ds,top=top,pitch=bottom['r2']-bottom['r1']+1+my-bottom['r2']-1)
  counts=list(map(len,ds));return f.render(g,st,sum(counts) if name=='sum' else max(counts))
 if CONFIG['parameter']=='render':return a.G.solve(g,name) if row['bank']=='current' else b.solve(g,name)
 if CONFIG['parameter']=='marker_pairing':
  if row['bank']=='current':return a.family.solve(g,row['settings'])
  return b.family.seal_top(a.family.solve(g,{'marker_pairing':'match'}))
 raise ValueError('unknown family')

@lru_cache(maxsize=64)
def matched_inputs(seed):
 candidates={'train':[],'test':[]};seen=set();rejected=[]
 for attempt in range(20):
  for bi,bank in enumerate(('current','incoming')):
   row=next(s for s in CONFIG['settings'] if s['bank']==bank)
   ep=BANKS[bank].generate(seed+attempt*100003,row['settings'],6,4)
   for split in ('train','test'):
    for p in ep[split]:
     g=p['input'];key=json.dumps(g)
     if key in seen:continue
     seen.add(key)
     try:ys=[predict(g,i) for i in range(len(CONFIG['settings']))]
     except (ValueError,TypeError,KeyError,IndexError,StopIteration) as e:rejected.append(dict(bank=bank,split=split,error=str(e)));continue
     candidates[split].append((g,ys,bank))
  remaining={(i,j) for i in range(len(CONFIG['settings'])) for j in range(i)};tr=[];used=set()
  for _ in range(2):
   scores=[sum(ys[i]!=ys[j] for i,j in remaining) if n not in used else -1 for n,(g,ys,bank) in enumerate(candidates['train'])]
   if not scores:break
   n=max(range(len(scores)),key=lambda n:(scores[n],candidates['train'][n][2] not in {x[2] for x in tr}));used.add(n);tr.append(candidates['train'][n]);ys=tr[-1][1];remaining={p for p in remaining if ys[p[0]]==ys[p[1]]}
  if remaining:continue
  tr += [x for n,x in enumerate(candidates['train']) if n not in used][:4]
  # One constructor per episode for query diversity; demos may bridge domains.
  bank=('current','incoming')[seed%2];te=[x for x in candidates['test'] if x[2]==bank][:4]
  if len(tr)==6 and len(te)==4:return tr,te,rejected
 raise ValueError('matched teaching sampler exhausted')

def generate(seed,settings,demos,queries):
 row=selected(settings);idx=CONFIG['settings'].index(row)
 for x,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(x)is not int or not lo<=x<=hi:raise ValueError('unsupported exact integer request')
 tr,te,_=matched_inputs(seed);order=list(range(4));random.Random(f'repeat-private-order:{seed}').shuffle(order)
 pair=lambda x:dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][idx]))
 return dict(train=[pair(x) for x in tr[:demos]],test=[pair(te[i]) for i in order[:queries]],program_solution=program(settings))
