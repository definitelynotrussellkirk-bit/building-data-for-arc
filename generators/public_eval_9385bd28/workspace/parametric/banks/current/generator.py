"""Input-only generator for public parent 9385bd28."""
from pathlib import Path
import hashlib
import importlib.util
import sys

RULE_TASK_ID = 'ee_9385bd28'
TASK_ID = GENERATOR_ID = 'public_eval_9385bd28'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Use a two-column color key to combine matching source fragments into layered rectangles.'
AXES = {'grid_h':{'type':'int','valid':'19..30','default':'scheduled'},
        'grid_w':{'type':'int','valid':'26..30','default':'scheduled'}}


def _engine():
    path=Path(__file__).resolve().parent/'workspace/parametric/engine.py'
    key='_public_9385_engine_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec)
        sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]


def generate(seed=0,sample_index=0,difficulty=None,**overrides):
    e=_engine();e.integer(seed,0,2**63-1,'seed');e.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if set(overrides)-{'grid_h','grid_w'}:raise ValueError('Unknown controls')
    if overrides:
        h=overrides.get('grid_h',24);w=overrides.get('grid_w',28)
        e.integer(h,19,30,'grid_h');e.integer(w,26,30,'grid_w')
        for attempt in range(128):
            try:return e._candidate(seed,sample_index,'production',h,w,attempt)
            except ValueError:pass
        raise ValueError('Bounded exact-size sampler exhausted')
    return e.make_input(seed,sample_index,'production',stress=difficulty=='hard' or sample_index%4==3)


def self_check(grid,*,difficulty=None,meta=None):return _engine().self_check(grid)
