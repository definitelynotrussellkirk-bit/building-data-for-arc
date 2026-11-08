"""Canonical-only public family generator, pending owner registration and approval."""
from pathlib import Path
import importlib.util,sys
from puzzle_generators.base import gen_ctx
RULE_TASK_ID = 'ee_b5ca7ac4'
GENERATOR_ID='public_eval_b5ca7ac4'
TASK_ID='public_eval_b5ca7ac4'
VERSION='1.0.0'
SUMMARY='Recover solid framed rectangles and cascade horizontal packing by frame color.'
INVARIANTS=['Unique majority background','Uniform 2/8 frames with different uniform interiors','Nonoverlapping input boxes']
AXES={}
_spec=importlib.util.spec_from_file_location('_b5ca7ac4_generator_prototype',Path(__file__).resolve().parent/'workspace/parametric/prototype.py')
P=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=P;_spec.loader.exec_module(P)

def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if overrides:raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return P.scene(seed,sample_index,rng=ctx.draw_rng('geometry'))

def self_check(grid):
    try:
        boxes=P.extract(grid);bg=P.background(grid)
        valid=bool(boxes) and bg not in (2,8) and P.paint(len(grid),len(grid[0]),bg,boxes)==grid
        return [] if valid else ['Expected nonoverlapping framed rectangles on a uniform background']
    except (TypeError,ValueError) as exc:return [str(exc)]
