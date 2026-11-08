"""Canonical translation-jigsaw scene generator; no public fixtures at runtime."""
RULE_TASK_ID = 'ee_4e34c42c'
from pathlib import Path
import importlib.util
from puzzle_generators.base import gen_ctx

GENERATOR_ID=TASK_ID='public_eval_4e34c42c'
VERSION='1.0.0'
SUMMARY='Reassemble disconnected overlapping fragments using shared multicolor patterns and crop the completed drawing.'
AXES={}
HELPFUL_TEXTURES=()
DEGENERATE_TEXTURES=()
INVARIANTS=['modal background','nonoverlapping input fragments','translation-only compatible assembly','fresh generated motifs']
_spec=importlib.util.spec_from_file_location('_public_jigsaw_generator',Path(__file__).parent/'workspace/parametric/prototype.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise ValueError(f'unknown override(s): {sorted(overrides)}')
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:raise ValueError('seed and sample_index require nonnegative integers')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty)
    derived=ctx.draw_rng('scene').getrandbits(63)
    return _model.scene(derived,sample_index,stress=sample_index%4==3)[0]


def rule_mirror(grid):return _model.solve(grid)


def self_check(grid,*,difficulty=None,meta=None):
    try:
        _model.validate_grid(grid)
        if len(_model.components(grid,_model.background(grid)))<2:return ['need at least two disconnected fragments']
        _model.validate_grid(_model.solve(grid))
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
