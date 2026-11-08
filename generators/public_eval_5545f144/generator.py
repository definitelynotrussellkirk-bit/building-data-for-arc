"""Faithful public 5545f144 route completion; labels are supplied by reference.rkt."""
from pathlib import Path
import importlib.util
import hashlib
from puzzle_generators.base import gen_ctx
TASK_ID=GENERATOR_ID='public_eval_5545f144'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH=hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY='Extract the cursor motif, follow nearest aligned waypoints, rotate it to the final leg and render the clean final panel.'
INVARIANTS=['one isolated reflection-symmetric cursor in the first panel','unique rotated cursor in the final panel','unique nearest aligned route','all grids at most 30 by 30']
AXES={}
spec=importlib.util.spec_from_file_location('public_eval_waypoint_base',Path(__file__).parent/'workspace/parametric/family.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise TypeError('no override axes')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if type(seed)!=int or seed<0 or type(sample_index)!=int or sample_index<0:raise ValueError('nonnegative integer seed/index required')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID)
    profile=ctx.draw_rng('profile').choice(((12,13,2),(16,14,2),(20,11,2),(30,30,1)))
    for attempt in range(512):
        try:return family._scene(seed,'base.'+str(sample_index),profile,attempt)
        except (ValueError,IndexError):pass
    raise RuntimeError('bounded scene search exhausted')
def rule_mirror(grid):return family.render(family.analyze(grid))
def self_check(grid):
    try:family.analyze(grid);return []
    except (ValueError,IndexError) as exc:return [str(exc)]

RULE_TASK_ID = 'ee_5545f144'
