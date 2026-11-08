"""Accepted observed-precedence branch plus explicit fragmentation alternatives."""
from pathlib import Path
import importlib.util,hashlib,sys,json,copy,random,itertools
from functools import lru_cache
BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/'union-config.json').read_text())
def load(rel):
 p=BASE/rel;n='_union19_'+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
C=load('banks/current/workspace/parametric/adapter.py');A=load('banks/current/workspace/parametric/audit.py');N=load('banks/extra/workspace/parametric/adapter.py')
model=C.model
sample_input=C.sample_input
MODES=tuple(CONFIG['modes'])
def selected(settings):
 if type(settings)is not dict or set(settings)!={'crossing_policy'}or type(settings['crossing_policy'])is not str or settings['crossing_policy']not in MODES:raise ValueError('one exact declared crossing policy required')
 return settings['crossing_policy']
def program(settings):
 mode=selected(settings);return(C if mode in C.MODES else N).program(settings)
def predict(g,mode):return C.model.solve(g,mode)if mode in C.MODES else N.E.solve(g,mode)
def rivals(g,mode):
 if mode in C.MODES:return A.rivals(g,mode)
 result={n:N.E.solve(g,mode,rival=n)for n in ('zero_fragment_count','pixel_count','ignore_yellow','global_ray')}
 result['opposite_fragment_policy']=N.E.solve(g,'complete'if mode=='fragmented'else'fragmented');result['identity']=copy.deepcopy(g)
 result['observed_reverse']=C.model.solve(g,'reverse_marked');result['observed_preserve']=C.model.solve(g,'preserve_visible');return result
def extra_damage(grid,seed):
 data=C.model.analyze(grid)
 signature=lambda d:({p['color']:(frozenset(p['cells']),p['marked'])for p in d['paths']},d['observed_under_over'])
 want=signature(data);cells=[]
 for r,row in enumerate(grid):
  for c,v in enumerate(row):
   if v in(0,2,4)or not(0<r<len(grid)-1 and 0<c<len(row)-1):continue
   if(grid[r-1][c]==grid[r+1][c]==v)or(grid[r][c-1]==grid[r][c+1]==v):cells.append((r,c))
 random.Random(f'faa19-extra-hole:{seed}').shuffle(cells)
 for n in range(min(24,len(cells))):
  out=copy.deepcopy(grid)
  for r,c in cells[n:n+1+(n%2)]:out[r][c]=0
  try:
   C.model.validate(out)
   if signature(C.model.analyze(out))==want:yield out
  except(ValueError,TypeError,IndexError):continue

def compatible_small_queries(seed):
 result=[];seen=set()
 for index in range(100,356):
  try:
   g=N.E.make(seed,index,False);C.model.validate(g)
  except(ValueError,TypeError,IndexError,AssertionError,RuntimeError):continue
  token=json.dumps(g)
  if token not in seen:result.append(g);seen.add(token)
  if len(result)==3:return result
 raise ValueError('bounded compatible small-bank construction exhausted')

@lru_cache(maxsize=64)
def inputs(seed):
 current=C.generate(seed,CONFIG['default'],6,4)
 def pack(p,bank):
  # Both parser domains must be defined; labels come from each explicitly named
  # branch. Fragmentation is not asserted equivalent to incumbent semantics.
  C.model.validate(p['input']);return(p['input'],[predict(p['input'],m)for m in MODES],bank)
 tr=[pack(p,'current')for p in current['train']]
 te=[pack(p,'current')for p in current['test']]
 if seed%2:
  large=next(x for x in te if len(x[0])==len(x[0][0])==30)
  te=[pack({'input':g},'compatible-fragmentation')for g in compatible_small_queries(seed)]+[large]
 covers=[]
 for attempt in range(4):
  for g,ys,bank in tr[len(covers):]:
   cover=set()
   for i,m in enumerate(MODES):
    for name,y in rivals(g,m).items():
     if y!=ys[i]:cover.add((m,name))
    for j in range(i):
     if ys[i]!=ys[j]:cover.add(('setting',i,j))
   covers.append(cover)
  needed=set().union(*covers)|{('fragmented','global_ray'),('complete','global_ray')};pair=next(((i,j)for i,j in itertools.combinations(range(len(tr)),2)if covers[i]|covers[j]==needed),None)
  if pair is not None:break
  more=C.generate((seed+attempt*104729)%(2**63),CONFIG['default'],2,4)
  for i,p in enumerate(more['train']):
   tr.extend(pack({'input':g},'extra-supported-damage')for g in extra_damage(p['input'],seed+attempt*2+i))
 if pair is None:
  best=min(itertools.combinations(range(len(covers)),2),key=lambda ij:len(needed-(covers[ij[0]]|covers[ij[1]])));raise ValueError('no two-demo finite-rival cover: '+repr((best,needed-(covers[best[0]]|covers[best[1]]))))
 order=list(pair)+[i for i in range(len(tr))if i not in pair];tr=[tr[i]for i in order[:6]]
 if len({json.dumps(x[0])for x in tr+te})!=10:raise ValueError('ten distinct input grids required')
 return tr,te,[]
def generate(seed,settings,demos=2,queries=4):
 mode=selected(settings)
 for n,lo,hi in((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
  if type(n)is not int or not lo<=n<=hi:raise ValueError('unsupported exact-integer request')
 tr,te,_=inputs(seed);order=list(range(4));random.Random(f'faa9f03d:union19:{seed}').shuffle(order);i=MODES.index(mode)
 def pair(x):return dict(input=copy.deepcopy(x[0]),output=copy.deepcopy(x[1][i]))
 return dict(train=[pair(x)for x in tr[:demos]],test=[pair(te[j])for j in order[:queries]],program_solution=program(settings))
def public_view(ep,index=0):
 if type(index)is not int or not 0<=index<len(ep['test']):raise ValueError('invalid query index')
 return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in ep['train']],test=[dict(input=ep['test'][index]['input'])]))
def __getattr__(name):return getattr(C,name)
