"""Fresh hollow-cross inputs for the da515329 spiral rule."""
from pathlib import Path
import importlib.util,sys
from puzzle_generators.base import gen_ctx
RULE_TASK_ID = 'ee_da515329'
VERSION='1.0.0';TASK_ID=GENERATOR_ID='public_eval_da515329'
SUMMARY='Extend a hollow-centered cross into four contact-avoiding symmetric spiral arms.'
INVARIANTS=['Black background','One equal-arm hollow-centered cross','Output preserves canvas size']
AXES={}
_spec=importlib.util.spec_from_file_location('_da515329_family',Path(__file__).resolve().parent/'workspace/parametric/family.py')
F=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=F;_spec.loader.exec_module(F)
def generate(seed,sample_index=0,difficulty=None,**overrides):
    if overrides:raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return F.scene(seed,sample_index,query=False)
def self_check(grid):
    try:
        color,_,_=F.parse_cross(grid);out=F.complete_spiral(grid);groups=F.components_of(out,color);sizes=sorted((len(x) for x in groups),reverse=True)
        return [] if len(sizes)>=3 and sizes[0]>sizes[1] else ['Expected unique longest completed spiral component']
    except (ValueError,TypeError) as exc:return [str(exc)]
