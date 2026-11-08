"""Fresh table-and-hollow-frame inputs for public parent dbff022c."""
from pathlib import Path
import importlib.util,sys
from puzzle_generators.base import gen_ctx
RULE_TASK_ID = 'ee_dbff022c'
VERSION='1.0.0';TASK_ID=GENERATOR_ID='public_eval_dbff022c'
SUMMARY='Use a small color correspondence table to fill enclosed single-color holes.'
INVARIANTS=['Black background','One filled 2xN or Nx2 color table','Mapped and unmapped hollow frames']
AXES={}
_spec=importlib.util.spec_from_file_location('_dbff022c_family',Path(__file__).resolve().parent/'workspace/parametric/family.py')
F=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=F;_spec.loader.exec_module(F)
def generate(seed,sample_index=0,difficulty=None,**overrides):
    if overrides:raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return F.scene(seed,sample_index,query=False)
def self_check(grid):
    try:
        F.analyze(grid);mid=F.causal_intermediate(grid)
        return [] if mid['dominant_fill']!=mid['raw_frequency_fill'] else ['Filled-area and raw-frame rankings must differ']
    except (ValueError,TypeError) as exc:return [str(exc)]
