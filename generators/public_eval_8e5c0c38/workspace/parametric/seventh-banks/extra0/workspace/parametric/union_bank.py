"""Episode-fixed disjoint rules on a private, matched multi-constructor bank.

The setting-independent intersection gate requires all retained defaults to agree,
all declared programs to be total, and redundant alternates to agree. Python
outputs are claims, always independently checked by protected native Racket.
"""
from pathlib import Path
import importlib.util,hashlib,sys,json,random,copy
from functools import lru_cache
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'union-config.json').read_text())
MODES=CONFIG['modes']
BANKS=[]
for i in range(len(CONFIG['banks'])):
 p=BASE/'banks'/f'bank{i}'/'workspace/parametric/adapter.py'
 n='_union_bank_'+hashlib.sha256(str(p).encode()).hexdigest()
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);BANKS.append(m)

def mode(settings):
 if type(settings) is not dict or set(settings)!={'rule'} or settings['rule'] not in MODES:raise ValueError('one declared episode rule is required')
 return MODES.index(settings['rule'])

def program(settings):
 i,j=CONFIG['active'][mode(settings)]
 return (BASE/('canonical.rkt' if (i,j)==(0,0) else f'bank{i}-program{j}.rkt')).read_text()

def predict(i,j,g):
 m=BANKS[i];s=CONFIG['banks'][i]['default' if j==0 else 'alternate'];v=next(iter(s.values()));t=CONFIG['task']
 if t=='2b83f449':return (m.CORE.solve(g,v) if i==0 else m.G.solve(g,v) if i==1 else m.model.solve(g,v))
 if t=='8e5c0c38':return m._module.solve(g,v) if i==0 else m.predict(g,s)
 if t=='8698868d':return m._native.solve(g,v) if i==0 else m.family.solve(g,v)
 if t=='136b0064':return m.mirror(g,s) if i==0 else m.family.solve(g,v)
 if t=='3a25b0d8':return m.impl.solve(g,v) if i==0 else m.family.solve(g,v)
 raise AssertionError(t)

def normalize(g,i):
 g=copy.deepcopy(g)
 if CONFIG['task']=='136b0064' and i==0:
  # Common-domain symbol semantics: use each glyph's original opcode color.
  parsed=BANKS[0].module.BASE.parse(g);ink={'R3':1,'L2':2,'L4':3,'D2':6}
  for op in parsed['slots']:
   for dr in range(3):
    for dc in range(3):
     r,c=4*op['row']+dr,4*op['column']+dc
     if g[r][c]:g[r][c]=ink[op['opcode']]
 return g

def table(g):
 try:
  allvalues=[[predict(i,j,g) for j in (0,1)] for i in range(len(BANKS))]
  if any(v[0]!=allvalues[0][0] for v in allvalues[1:]):return None
  if len(MODES)==2 and any(v[1]!=allvalues[0][1] for v in allvalues[1:]):return None
  return [allvalues[i][j] for i,j in CONFIG['active']]
 except (ValueError,TypeError,KeyError,IndexError,AssertionError,StopIteration):return None

def rng(seed,role):
 return random.Random(int.from_bytes(hashlib.sha256(f"{CONFIG['task']}:{seed}:{role}".encode()).digest(),'big'))

@lru_cache(maxsize=64)
def inputs(seed):
 candidates={'train':[],'test':[]};seen=set()
 for attempt in range(24):
  for bi,b in enumerate(BANKS):
   ep=b.generate(seed+attempt*100003,CONFIG['banks'][bi]['default'],6,4)
   for split in ('train','test'):
    for pair in ep[split]:
     g=normalize(pair['input'],bi);k=json.dumps(g)
     if k in seen:continue
     seen.add(k);ys=table(g)
     if ys is not None:candidates[split].append((g,ys,bi))
  # Select demos only from demonstration candidates; query outputs never select lessons.
  remaining={(i,j) for i in range(len(MODES)) for j in range(i)};selected=[];used=set()
  for k in range(2):
   scores=[sum(ys[i]!=ys[j] for i,j in remaining) if n not in used else -1 for n,(g,ys,bi) in enumerate(candidates['train'])]
   if not scores:break
   best=max(range(len(scores)),key=lambda n:(scores[n], int(candidates['train'][n][2] not in {x[2] for x in selected})))
   used.add(best);selected.append(candidates['train'][best]);ys=selected[-1][1];remaining={p for p in remaining if ys[p[0]]==ys[p[1]]}
  if remaining:continue
  # Keep every constructor represented in the full demo/query banks where available.
  rest=[x for n,x in enumerate(candidates['train']) if n not in used];rng(seed,'extra-demos').shuffle(rest)
  selected+=rest[:4]
  pools=[[x for x in candidates['test'] if x[2]==bi] for bi in range(len(BANKS))]
  if len(selected)<6 or any(not p for p in pools):continue
  queries=[]
  for k in range(4):
   bi=k%len(BANKS);pool=[x for x in pools[bi] if x not in queries]
   if not pool:break
   queries.append(rng(seed,f'query-pick-{k}').choice(pool))
  if len(queries)<4:continue
  rng(seed,'private-query-order').shuffle(queries)
  return selected,queries
 raise RuntimeError('Common-domain, teaching or bank coverage sampler exhausted')

def generate(seed,settings,demos,queries):
 mi=mode(settings)
 for value,lo,hi in [(seed,0,2**63-1),(demos,2,6),(queries,1,4)]:
  if type(value)is not int or not lo<=value<=hi:raise ValueError('unsupported exact integer request')
 train,test=inputs(seed)
 def pairs(xs):return [dict(input=copy.deepcopy(g),output=copy.deepcopy(ys[mi])) for g,ys,bi in xs]
 return dict(train=pairs(train[:demos]),test=pairs(test[:queries]),program_solution=program(settings))

def public_view(episode,index):
 if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=episode['train'],test=[dict(input=episode['test'][index]['input'])]))
