"""Canonical-only production entry point; authoring source pending owner review."""
from pathlib import Path
import importlib.util
import sys
from puzzle_generators.base import gen_ctx
RULE_TASK_ID = 'ee_dfadab01'
VERSION='1.0.0'
TASK_ID='public_eval_dfadab01'
GENERATOR_ID='public_eval_dfadab01'
SUMMARY='Expand geometric symbol codes; omit southeast legend labels.'
INVARIANTS=['Black canvas', 'Four fixed geometric symbol codes', 'At least one nonlegend target']
AXES={}
_spec=importlib.util.spec_from_file_location('_dfadab01_generator_prototype',Path(__file__).resolve().parent/'workspace/parametric/prototype.py')
P=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=P;_spec.loader.exec_module(P)

def generate(seed, sample_index=0, difficulty=None, **overrides):
    if overrides:raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return P.scene(seed,sample_index,rng=ctx.draw_rng('geometry'))

def self_check(grid):
    try:
        P.checked_grid(grid)
        return [] if P.targets(grid) else ['Expected at least one nonlegend target']
    except (ValueError,TypeError) as exc:return [str(exc)]
