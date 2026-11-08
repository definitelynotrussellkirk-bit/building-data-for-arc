"""Fresh marker-relative copying scenes, labelled by the Racket reference."""
import importlib.util
from pathlib import Path
GENERATOR_ID = 'public_eval_7ed72f31'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_7ed72f31'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Copy local objects across their red mirror line or red half-turn center.'
AXES = {}
INVARIANTS = ['red markers and locally attached sources','collision-free reflected and rotated copies']
_spec=importlib.util.spec_from_file_location('marker_7ed72f31_generator',Path(__file__).resolve().parent/'workspace/parametric/family.py')
_family=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_family)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'): raise ValueError('Unknown difficulty')
    if overrides: raise TypeError('No generation overrides are declared')
    return _family.sample(seed,sample_index,stress=(difficulty=='hard'))
def self_check(grid,*,difficulty=None,meta=None):
    try:
        _family.analyze(grid)
        return []
    except (ValueError,TypeError,IndexError) as exc:
        return [str(exc)]
