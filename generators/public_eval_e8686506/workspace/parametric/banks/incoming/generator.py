"""Input-only generator for translation-only colored exact-cover assembly."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_e8686506'
TASK_ID = 'public_eval_e8686506'
GENERATOR_ID = TASK_ID
VERSION = '1.0.0'
SUMMARY = 'Scatter orientation-preserving colored pieces around a largest-object target skeleton.'
AXES = {}
INVARIANTS = ['Unique dominant background', 'Largest tied monochrome 8-components form the target',
              'Every loose piece is used exactly once, by translation only',
              'Constructed holes have a unique colored exact cover']

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_e8686506_generator_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if overrides:raise ValueError('no controls are declared; unknown overrides are rejected')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    return _adapter().scene(seed,sample_index)

def self_check(g):
    try:return _adapter().color_solution_count(g,limit=2)==1
    except (ValueError,TypeError,IndexError):return False
