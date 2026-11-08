"""Input-only generator for the public multicolor motif expansion parent."""
import hashlib,importlib.util,sys
from pathlib import Path
GENERATOR_ID = TASK_ID = 'public_eval_bf45cf4b'
RULE_TASK_ID = 'ee_bf45cf4b'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Infer the monochrome layout and multicolor motif, then expand occupied layout cells by complete motif tiles.'
AXES = {'grid_h':{'type':'int','valid':'14..30'},'grid_w':{'type':'int','valid':'14..30'},
        'mask_h':{'type':'int','valid':'3..6'},'mask_w':{'type':'int','valid':'3..6'},
        'motif_h':{'type':'int','valid':'3..6'},'motif_w':{'type':'int','valid':'3..6'},
        'axis':{'type':'enum','valid':['horizontal','vertical','both']},'motif_colors':{'type':'int','valid':'2..3'}}
INVARIANTS=['unique modal background','separated color-role panels','multicolor motif','output dimensions at most 30x30']

def _adapter():
    p=Path(__file__).resolve().parent/'workspace/parametric/adapter.py';key='_motif_generator_'+hashlib.sha256(str(p).encode()).hexdigest()[:16]
    if key not in sys.modules:
        s=importlib.util.spec_from_file_location(key,p);m=importlib.util.module_from_spec(s);sys.modules[key]=m;s.loader.exec_module(m)
    return sys.modules[key]

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('Unknown controls')
    if difficulty=='easy':
        overrides.setdefault('mask_h',3);overrides.setdefault('mask_w',3);overrides.setdefault('motif_h',3);overrides.setdefault('motif_w',3)
    if difficulty=='hard':
        overrides.setdefault('mask_h',6);overrides.setdefault('mask_w',5);overrides.setdefault('motif_h',5);overrides.setdefault('motif_w',6)
    return _adapter().sampler.draw(seed,sample_index,split='production',**overrides)

def self_check(grid,*,difficulty=None,meta=None):
    try:_adapter().model.analyze(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
