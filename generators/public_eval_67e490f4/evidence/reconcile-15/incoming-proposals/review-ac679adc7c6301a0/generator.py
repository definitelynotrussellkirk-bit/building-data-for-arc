"""Public 67e490f4: perforated-template shape-class vote inputs."""
RULE_TASK_ID = 'ee_67e490f4'
from pathlib import Path
import hashlib
import importlib.util

TASK_ID = GENERATOR_ID = 'public_eval_67e490f4'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Match outside pieces to template slots under D4 symmetry and fill each slot with its shape-class modal color.'
INVARIANTS = [
    'unique largest full-border perforated template',
    'at least three shape classes with class-specific vote histograms',
    'outside pieces and template holes match under full D4 symmetry',
    'all grids are bounded by 30x30',
]
AXES = {}
PROGRAM = Path(__file__).with_name('reference.rkt').read_text(encoding='utf-8')
RULE_HASH = hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
_path = Path(__file__).parent / 'workspace/parametric/model.py'
_spec = importlib.util.spec_from_file_location('public_eval_67e490f4_base', _path)
family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if overrides:
        raise TypeError('No undeclared override axes')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unknown difficulty')
    if (type(seed) is not int or isinstance(seed, bool) or not 0 <= seed < 2**63
            or type(sample_index) is not int or isinstance(sample_index, bool) or sample_index < 0):
        raise ValueError('Expected nonnegative integer seed/index')
    stress = difficulty == 'hard' or sample_index % 3 == 2
    return family.scene(seed, f'base:{sample_index}:{difficulty}', stress=stress)


def rule_mirror(grid):
    return family.solve(grid, 'modal')


def self_check(grid, **_):
    try:
        family.analyze(grid)
        return []
    except (ValueError, IndexError, TypeError) as error:
        return [str(error)]
