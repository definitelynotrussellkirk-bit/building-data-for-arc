import sys,time
sys.path.insert(0,'generators/1dd0439f7260/workspace/parametric')
from prototype import _sample,program_for
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
with RacketBridge() as b:
 for i in (0,1,5):
  grid,_labels,_,_=_sample(0,i,6,'medium')
  for mode in ('all','closest_spokes','farthest_spokes'):
   b.define_grid('g',grid)
   st=time.perf_counter()
   y=b.eval_text(f'({wrap_rule(program_for(mode))} g)')
   print(i,mode,len(grid),len(grid[0]),round(time.perf_counter()-st,3),flush=True)
