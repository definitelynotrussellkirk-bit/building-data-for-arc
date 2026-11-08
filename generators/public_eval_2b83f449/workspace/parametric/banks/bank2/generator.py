"""Input-only canonical generator for public ARC gate-path parent 2b83f449."""
from pathlib import Path
import hashlib
import importlib.util
import sys
GENERATOR_ID = TASK_ID = 'public_eval_2b83f449'
RULE_TASK_ID = 'ee_2b83f449'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Open orange gates, derive nonbranching cyan paths, and pack green markers at each lower endpoint.'
AXES={
 'grid_h':{'type':'int','valid':'9..30','default':'scheduled'},
 'grid_w':{'type':'int','valid':'16..30','default':'scheduled'},
 'holes':{'type':'int','valid':'0..4','default':'0..2'},
 'gates_per_lane':{'type':'int','valid':'1..3 when geometrically feasible','default':'1..3'},
 'reflection':{'type':'int','valid':'0..3','default':'horizontal/vertical'},
 'phase':{'type':'int','valid':'0..1','default':'cyan-row offset'}
}
INVARIANTS=['horizontal orange triples between cyan rows','green markers at path endpoints','gate-derived cyan components have degree at most 2','green population conserved']

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py';key='_gate_generator_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('Unknown controls')
    if difficulty is not None:
        overrides.setdefault('grid_h',{'easy':11,'medium':21,'hard':30}[difficulty])
        overrides.setdefault('grid_w',{'easy':16,'medium':24,'hard':30}[difficulty])
    return _adapter().sampler.draw(seed,sample_index,split='production',**overrides)

def self_check(grid,*,difficulty=None,meta=None):
    try:_adapter().model.analyze(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
