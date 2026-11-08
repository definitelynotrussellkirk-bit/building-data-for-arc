"""Public 9aaea919: count donor units, then extend receiver stacks."""
from pathlib import Path
import importlib.util
import sys
from puzzle_generators.base import gen_ctx
RULE_TASK_ID = 'ee_9aaea919'
VERSION = '1.0'
EXAMPLES_NEEDED = 2
_BASE=Path(__file__).resolve().parent/'workspace/parametric'
_SPEC=importlib.util.spec_from_file_location('_generator_9aa_core',_BASE/'core.py')
_CORE=importlib.util.module_from_spec(_SPEC); sys.modules[_SPEC.name]=_CORE; _SPEC.loader.exec_module(_CORE)

def generate(seed=0, sample_index=0, difficulty=None, **overrides):
    _CORE.integer(seed,0,2**63-1,'seed'); _CORE.integer(sample_index,0,2**31-1,'sample_index')
    if overrides or difficulty not in (None,'easy','medium','hard'):
        raise ValueError('Unknown generator controls')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=RULE_TASK_ID,difficulty=difficulty)
    return _CORE.build(ctx.draw_int('scene_seed',0,2**31-1),sample_index)

def self_check(grid):
    try: _CORE.analyze(grid)
    except (ValueError,TypeError,IndexError) as exc: return [str(exc)]
    return []
