"""Unapproved binary-defect generator; labels are supplied by reference.rkt."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_71e489b6'
VERSION = '1.0.0'
TASK_ID = 'public_eval_71e489b6'
GENERATOR_ID = TASK_ID
SUMMARY = 'Outline thin black defects and remove stray blue impulses in binary fields.'
INVARIANTS = ['Binary rectangular grid, 16..30 per side', 'At least one structural blue component and one black defect', 'Four-query curricula cover blue and black dominant fields']
AXES = {}

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_71e489b6_generator_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    if overrides:raise ValueError('no controls are declared; unknown overrides are rejected')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    return _adapter().scene(seed,sample_index)

def self_check(g):
    try:
        a=_adapter();a.grid(g,binary=True)
        clean,holes,rim=a.analyze(g)
        if len(g)<8 or len(g[0])<8 or not holes or not rim:
            return ['Expected a structural binary field with a black defect and rim']
        if not any(a.has_core(o)for o in a.components({(r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v==1})):
            return ['Expected a structural blue component']
        return []
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
