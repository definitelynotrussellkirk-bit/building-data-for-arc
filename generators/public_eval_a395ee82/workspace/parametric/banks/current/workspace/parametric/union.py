"""Disjoint ink/holes/clockwise rules on a matched mixture of both returned banks."""
from pathlib import Path
import importlib.util
from copy import deepcopy
from functools import lru_cache
BASE=Path(__file__).resolve().parent

def _load(name):
 s=importlib.util.spec_from_file_location('a395_union_'+name,BASE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
one=_load('bank_one');two=_load('bank_two')
OPTIONS=('ink','holes','clockwise')

def setting(settings):
 if settings is None:return 'ink'
 if type(settings)!=dict:raise ValueError('settings must be a dictionary')
 if set(settings)=={'rule'} and settings['rule'] in OPTIONS:return settings['rule']
 if set(settings)=={'tile_mask'} and settings['tile_mask'] in ('ink','holes'):return settings['tile_mask']
 if set(settings)=={'layout'} and settings['layout'] in ('as_drawn','clockwise'):return 'ink' if settings['layout']=='as_drawn' else 'clockwise'
 raise ValueError('unknown setting')

def program(settings=None):
 mode=setting(settings);return (BASE/('canonical.rkt' if mode=='ink' else mode+'.rkt')).read_text()

def solve(g,mode):return two.solve(g,'clockwise') if mode=='clockwise' else one.solve(g,mode)

@lru_cache(maxsize=64)
def inputs(seed):
 demos=[one.scene(one.rng_for(seed,f'union-demo-{i}'),i) if i%2==0 else two.sample(seed,'train',i) for i in range(6)]
 queries=[one.scene(one.rng_for(seed,'union-query-small'),6),two.sample(seed,'test',1),one.scene(one.rng_for(seed,'union-query-stress'),9),two.sample(seed,'test',3)]
 one.rng_for(seed,'union-query-order').shuffle(queries)
 bank=demos+queries
 if len({repr(g) for g in bank})!=10:raise ValueError('duplicate bank inputs')
 for g in bank:
  two.parse(g)
  if one.solve(g)!=two.solve(g):raise ValueError('canonical authorities disagree on shared grammar')
 return bank

def generate(seed,settings=None,demos=3,queries=4):
 mode=setting(settings)
 for name,x,lo,hi in (('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)):
  if type(x)!=int or not lo<=x<=hi:raise ValueError('invalid '+name)
 bank=inputs(seed);pair=lambda g:dict(input=deepcopy(g),output=solve(g,mode))
 return {'train':[pair(g) for g in bank[:demos]],'test':[pair(g) for g in bank[6:6+queries]],'program_solution':program({'rule':mode})}

TWO_RIVALS=('unit_scale','square_scale','counterclockwise','transpose','reverse','first_only','keep_center_color','retain_diagram')

def two_rival_program(mode,name):
 p=(BASE/('clockwise.rkt' if mode=='clockwise' else 'incoming-canonical.rkt')).read_text()
 placement='(map (lambda (p) (list (second p) (- (first p)))) offsets)' if mode=='clockwise' else 'offsets'
 if name=='unit_scale':return p.replace('(define motif-h (obj-h source))','(define motif-h 1)').replace('(define motif-w (obj-w source))','(define motif-w 1)')
 if name=='square_scale':return p.replace('(define motif-w (obj-w source))','(define motif-w (obj-h source))')
 if name in ('counterclockwise','transpose','reverse','first_only'):
  new={'counterclockwise':'(map (lambda (p) (list (- (second p)) (first p))) offsets)','transpose':'(map (lambda (p) (list (second p) (first p))) offsets)','reverse':'(map (lambda (p) (list (- (first p)) (- (second p)))) offsets)','first_only':'(list (first '+placement+'))'}[name]
  return p.replace('(define placements '+placement+')','(define placements '+new+')')
 if name=='keep_center_color':return p.replace('(obj-cells source) mark-color)','(obj-cells source) source-color)')
 if name=='retain_diagram':return p.replace('(define blank (build-grid h w (r c) bg))','(define blank g)')
 raise ValueError(name)

def rivals(mode):
 result={}
 if mode in ('ink','holes'):
  result.update({'one/'+k:p for k,p in one.rival_programs({'tile_mask':mode}).items()})
 if mode in ('ink','clockwise'):
  result.update({'two/'+k:two_rival_program(mode,k) for k in TWO_RIVALS})
 result.update({'setting/'+other:program({'rule':other}) for other in OPTIONS if other!=mode})
 return result

def rival_predict(g,mode,name):
 group,name=name.split('/',1)
 if group=='one':return one.rival_predict(g,mode,name)
 if group=='two':return two.solve(g,'clockwise' if mode=='clockwise' else 'as_drawn',rival=name)
 return solve(g,name)
