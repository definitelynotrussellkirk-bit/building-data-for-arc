"""Canonical constructive generator: count-dependent clearances around barriers."""
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx
TASK_ID=GENERATOR_ID='public_eval_cb2d8a2c'
RULE_TASK_ID = 'ee_cb2d8a2c'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
SUMMARY='Count blue barrier markers, infer clearance waypoints, and route from the green boundary source.'
INVARIANTS=['one green boundary source','alternating edge-attached straight barriers','blue-count-plus-one clearance','legal unobstructed bypass lanes']
AXES={}
_spec=importlib.util.spec_from_file_location('_cb2d8a2c_generator',Path(__file__).parent/'workspace/parametric/model.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0 or overrides:
        raise ValueError('integer seed, nonnegative sample_index; no overrides')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return _model.scene(ctx.draw_rng('scene'),sample_index%10)
