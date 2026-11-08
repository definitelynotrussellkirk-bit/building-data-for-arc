"""Public fc7cae8d: crop and orient the picture by matching two frame edges."""
import importlib.util
from pathlib import Path
RULE_TASK_ID = 'ee_fc7cae8d'
TASK_ID = GENERATOR_ID = 'public_eval_fc7cae8d'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Match two colored frame edges to crop and orient an isolated picture.'
AXES = {}
INVARIANTS = ['two distinct adjacent guide colors', 'one isolated interior framed picture',
              'gray exterior noise', 'integer grids at most 30x30']
path = Path(__file__).resolve().parent/'workspace/parametric/family.py'
spec = importlib.util.spec_from_file_location('_fc7cae8d_generator_family',path)
family = importlib.util.module_from_spec(spec); spec.loader.exec_module(family)
PROGRAM = Path(__file__).with_name('reference.rkt').read_text()

def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError('Nonnegative integer seed/index required')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('Unsupported difficulty or override')
    size = {'easy':18,'medium':24,'hard':30}.get(difficulty, [18,22,26,30][sample_index%4])
    return family.scene(seed, f'base/{sample_index}', size)

def rule_mirror(grid):
    return family.solve(grid)

def self_check(grid):
    try:
        family.decode(grid)
        return []
    except ValueError as exc:
        return [str(exc)]
