"""Constructive canonical reflected rays for public parent 142ca369."""
RULE_TASK_ID = 'ee_142ca369'
import importlib.util
from pathlib import Path
from puzzle_generators.base import gen_ctx
TASK_ID=GENERATOR_ID='public_eval_142ca369'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
SUMMARY='L triominoes emit diagonal rays that reflect from centered singleton/bar mirrors and adopt each mirror color.'
INVARIANTS=['black background','L-triomino sources','singleton or length-three straight mirrors','original gadgets preserved']
AXES={}
_spec=importlib.util.spec_from_file_location('_142ca369_generator_model',Path(__file__).parent/'workspace/parametric/model.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0 or overrides:raise ValueError('integer seed/index; no overrides')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides={})
    return _model.scene(ctx.draw_rng('scene'),sample_index%10)
