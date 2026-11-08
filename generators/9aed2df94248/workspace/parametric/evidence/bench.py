import sys,time
sys.path.insert(0,'generators/9aed2df94248/workspace/parametric')
from prototype import _sample,program_for
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
with RacketBridge() as b:
 for i in (0,1,5):
  grid,_labels,code=_sample(0,i,6,'medium')
  for mode in ('once','twice','mirror_after'):
   b.define_grid('g',grid)
   st=time.perf_counter()
   y=b.eval_text(f'({wrap_rule(program_for(mode))} g)')
   print(i,mode,len(grid),len(grid[0]),round(time.perf_counter()-st,3),flush=True)
