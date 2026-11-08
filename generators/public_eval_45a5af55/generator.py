"""Public 45a5af55 row-strip to concentric-square generator. Not owner-approved."""
from pathlib import Path
import hashlib
import importlib.util
import sys

TASK_ID = GENERATOR_ID = 'public_eval_45a5af55'
RULE_TASK_ID = 'ee_45a5af55'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
PROGRAM = Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH = hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY = 'Fold constant-color rows into concentric square layers.'
INVARIANTS = ['constant-color rows', 'last row repeats the innermost retained color', 'output side is twice height minus two']
AXES = {}

PATH = Path(__file__).parent / 'workspace/parametric/family.py'
NAME = '_public_45a5af55_base_' + hashlib.sha256(str(PATH).encode()).hexdigest()
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
G = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = G
SPEC.loader.exec_module(G)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError('nonnegative exact integer seed and sample_index required')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('unsupported difficulty')
    if overrides:
        raise TypeError('no override axes')
    return G.ordinary(seed, sample_index, stress=(difficulty == 'hard' or sample_index % 10 == 9))


def rule_mirror(grid):
    return G.predict(grid, 'rings_only')


self_check = G.self_check
