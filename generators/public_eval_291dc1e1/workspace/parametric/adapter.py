"""Matched three-rule family retaining both source constructors and exact programs."""
from pathlib import Path
import importlib.util,hashlib,sys,json,random,copy
from functools import lru_cache
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'union-config.json').read_text());MODES=CONFIG['modes'];KEY=CONFIG['parameter'];TASK=CONFIG['task']
def load(bank):
 p=BASE/'banks'/bank/'workspace/parametric/adapter.py';n='_repeat_'+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
CURRENT=load('current');INCOMING=load('incoming')
def mode(settings):
 if type(settings)is not dict or set(settings)!={KEY}or settings[KEY]not in MODES:raise ValueError('exact declared setting required')
 return MODES.index(settings[KEY])
def program(settings):
 i=mode(settings)
 return CURRENT.program({KEY:MODES[i]}) if i<2 else INCOMING.program({'mode':'width_walk'}) if TASK=='291dc1e1' else (BASE/'largest.rkt').read_text()
def normalized(g):
 a=CURRENT.module.BASE.parse(g);colors={a['background']:1,a['foreground']:7,a['ray_color']:2}
 return [[colors[v]for v in row]for row in g],{v:k for k,v in colors.items()}
def largest(g):
 a=CURRENT.module.BASE.analyze(g,'union');out=[[a['background']]*a['width']for _ in range(a['height'])]
 for r,c in a['rays']:out[r][c]=a['ray_color']
 for r,c in a['anchors']:out[r][c]=a['foreground']
 regions=[r for r in a['regions']if r['selected']]
 if regions:
  region=max(regions,key=lambda r:len(r['cells']));dr,dc=region['shift']
  for r,c in region['cells']:out[r+dr][c+dc]=a['foreground']
 return out
def table(g):
 ys=[CURRENT.mirror(g,{KEY:v})for v in MODES[:2]]
 if TASK=='291dc1e1':
  if INCOMING._source.solve(g,'canonical')!=ys[0]:raise ValueError('canonical authority disagreement')
  return ys+[INCOMING._source.solve(g,'width_walk')]
 return ys+[largest(g)]
def rival_keys():
 if TASK=='291dc1e1':return [(i,r)for i in (0,2)for r in INCOMING._source.RIVALS if i==2 or r not in ('raw_width','fixed_first_stride','global_max_stride','unit_stride')]
 return [(i,r)for i in (0,2)for r in INCOMING.G.RIVALS if r!=('all_sectors'if i==0 else'largest_sector')]
def rival(g,i,r):
 if TASK=='291dc1e1':return INCOMING._source.solve(g,'canonical'if i==0 else'width_walk',rival=r)
 norm,colors=normalized(g)
 return [[colors[v]for v in row]for row in INCOMING.G.solve(norm,'all'if i==0 else'largest',rival=r)]
def cover(item):
 g,ys,bi=item;out=set()
 for i,r in rival_keys():
  try:wrong=rival(g,i,r)
  except ValueError:continue
  if wrong!=ys[i]:out.add((i,r))
 for i in range(3):
  for j in range(i):
   if ys[i]!=ys[j]:out.add(('mode',i,j))
 return out
def rng(seed,role):return random.Random(f'{TASK}:{seed}:{role}')
@lru_cache(maxsize=64)
def inputs(seed):
 # Keep the complete current three-lesson prefix. The incoming two-lesson
 # prefix then teaches its new rule's rivals, without inspecting any query.
 old=CURRENT.generate(seed,{KEY:MODES[0]},6,4)
 new=INCOMING.generate(seed,{'mode':'canonical'}if TASK=='291dc1e1'else{'selection':'all'},6,4)
 train=[];rejected=[]
 for bi,ep in enumerate([old,new]):
  for p in ep['train']:
   try:ys=table(p['input'])
   except (ValueError,IndexError,KeyError,AssertionError)as e:rejected.append(dict(bank=bi,split='train',error=str(e)));continue
   train.append((p['input'],ys,bi))
 # Retain current first three; add the two incoming teaching profiles.
 required=set(rival_keys())|{('mode',i,j)for i in range(3)for j in range(i)}
 # Preserve the incumbent first two profiles (complementary axes). Search only
 # demonstration candidates for the third lesson to cover the remaining rivals.
 selected=train[:2];remaining=required-set().union(*(cover(x)for x in selected))
 rest=[x for x in train if x not in selected]
 for attempt in range(32):
  candidates=rest
  best=max(candidates,key=lambda x:len(cover(x)&remaining))
  if remaining<=cover(best):selected.append(best);break
  ep=INCOMING.generate(seed+100003*(attempt+1),{'mode':'canonical'}if TASK=='291dc1e1'else{'selection':'all'},6,4)
  for pair in ep['train']:
   try:rest.append((pair['input'],table(pair['input']),1))
   except ValueError:continue
 else:raise ValueError('three-demo retained rival coverage exhausted: '+str(remaining))
 seen={json.dumps(x[0])for x in selected}
 for x in train:
  k=json.dumps(x[0])
  if k not in seen:seen.add(k);selected.append(x)
 selected=selected[:6]
 if len(selected)!=6:raise ValueError('insufficient demonstration bank')
 # Queries draw a complete episode from one constructor. This preserves its
 # single-cut/small/dense profiles and avoids forcing mixed-domain geometry.
 bi=seed%2;ep=[old,new][bi];queries=[]
 for p in ep['test']:
  ys=table(p['input']);queries.append((p['input'],ys,bi))
 rng(seed,'private-query-order').shuffle(queries)
 return selected,queries,rejected

def generate(seed,settings,demos,queries):
 mi=mode(settings)
 for v,lo,hi in [(seed,0,2**63-1),(demos,3,6),(queries,1,4)]:
  if type(v)is not int or not lo<=v<=hi:raise ValueError('invalid exact integer request')
 train,test,_=inputs(seed)
 def pairs(xs):return [dict(input=copy.deepcopy(g),output=copy.deepcopy(ys[mi]))for g,ys,bi in xs]
 return dict(train=pairs(train[:demos]),test=pairs(test[:queries]),program_solution=program(settings))
def public_view(ep,index):return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in ep['train']],test=[dict(input=ep['test'][index]['input'])]))
