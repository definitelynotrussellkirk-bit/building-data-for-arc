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

def self_check(g, *, difficulty=None):
    """Worker findings contract: valid inputs return [], never a success boolean."""
    try:
        a = _adapter()
        a.grid(g, binary=True)
        if not 16 <= len(g) <= 30 or not 16 <= len(g[0]) <= 30:
            return ['grid dimensions are outside the declared 16..30 range']
        _, holes, rim = a.analyze(g)
        if not holes or not rim:
            return ['sample must contain a black defect with a nonempty rim']
        blues = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 1}
        if not any(a.has_core(o) for o in a.components(blues)):
            return ['sample must contain a structural blue component']
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
