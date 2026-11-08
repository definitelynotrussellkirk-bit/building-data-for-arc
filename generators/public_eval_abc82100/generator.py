"""Faithful keyed-stencil substitution for public evaluation parent abc82100."""
import importlib.util
from pathlib import Path
RULE_TASK_ID = 'ee_abc82100'
TASK_ID = GENERATOR_ID = 'public_eval_abc82100'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Use two-color handles to replace source dots with cyan stencil shapes in the indicated paint colors.'
AXES = {}
INVARIANTS = ['cyan stencil masks', 'outer source and inner paint keys', 'simultaneous substitution',
              'clipped stamps; untouched unmapped dots', 'all grids at most 30x30']
path=Path(__file__).resolve().parent/'workspace/parametric/family.py'
spec=importlib.util.spec_from_file_location('_abc82100_generator_family',path)
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:
        raise ValueError('Nonnegative integer seed/index required')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('Unsupported difficulty or overrides')
    n={'easy':22,'medium':26,'hard':30}.get(difficulty,[22,24,26,30][sample_index%4])
    return family.scene(seed,f'base/{sample_index}',n,touching=sample_index%2==1)

def rule_mirror(grid):return family.solve(grid)

def self_check(grid):
    try:family.analyze(grid);return []
    except ValueError as exc:return [str(exc)]
