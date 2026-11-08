"""Input-only canonical generator for public ARC beam-relay parent 5961cc34."""
from pathlib import Path
import hashlib
import importlib.util
import sys

GENERATOR_ID = TASK_ID = 'public_eval_5961cc34'
RULE_TASK_ID = 'ee_5961cc34'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Trace red beams through reached blue relays using their green output ports; erase unreachable objects.'
AXES = {
 'grid_h':{'type':'int','valid':'24..30','default':'24..29'},
 'grid_w':{'type':'int','valid':'24..30','default':'24..29'},
 'path_id':{'type':'int','valid':'0..5','default':'scheduled'},
 'band':{'type':'int','valid':'1..2','default':'random'},
 'transform_id':{'type':'int','valid':'0..7','default':'D4'}
}
INVARIANTS=['one yellow emitter with a straight red tail','blue/green connected relays with one outward port','same-color background 8','inactive relays are erased']

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py';key='_beam_generator_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('Unknown controls')
    # Difficulty changes default topology; explicit controls retain exact meaning.
    if 'path_id' not in overrides and difficulty is not None:overrides['path_id']={'easy':4,'medium':1,'hard':5}[difficulty]
    return _adapter().sampler.draw(seed,sample_index,split='production',**overrides)

def self_check(grid,*,difficulty=None,meta=None):
    try:_adapter().model.parts(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
