"""Generate fresh colored support graphs without importing evaluation fixtures."""
from pathlib import Path
import importlib.util
from puzzle_generators.base import gen_ctx

GENERATOR_ID=TASK_ID='public_eval_b6f77b65'
RULE_TASK_ID = 'ee_b6f77b65'
VERSION='1.0.0'
SUMMARY='Erase the cue colors, then settle a nested graph of colored posts and bilaterally supported beams.'
AXES={}
HELPFUL_TEXTURES=()
DEGENERATE_TEXTURES=()
INVARIANTS=['zero background','cue row plus blank separator','axis-aligned support graph','no upward motion','occluded terminal endpoints']
_spec=importlib.util.spec_from_file_location('_public_support_generator',Path(__file__).parent/'workspace/parametric/prototype.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise ValueError(f'unknown override(s): {sorted(overrides)}')
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:raise ValueError('seed and sample_index require nonnegative integers')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty)
    derived=ctx.draw_rng('scene').getrandbits(63)
    return _model.scene(derived,sample_index,stress=sample_index%4==3)


def rule_mirror(grid):return _model.solve(grid)


def self_check(grid,*,difficulty=None,meta=None):
    try:
        _model.validate_grid(grid)
        if not any(grid[0]):return ['a removal cue is required']
        objects=_model.extract(grid)
        if not any(p['kind']=='beam' for p in objects):return ['need at least one beam']
        if not any(p['kind']=='post' for p in objects):return ['need at least one post']
        _model.validate_grid(_model.solve(grid))
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
