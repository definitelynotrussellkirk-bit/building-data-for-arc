"""Ordinary canonical input sampler; independent runtime supplies reference labels."""
from pathlib import Path
import importlib.util
import hashlib
import sys

TASK_ID = GENERATOR_ID = 'public_eval_9bbf930d'
RULE_TASK_ID = 'ee_9bbf930d'
VERSION = GENERATOR_VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
AXES = {}
SUMMARY = 'Trace magenta markers through colored corridors with input-dependent guidance updates.'
INVARIANTS = ['Canonical rule is reference.rkt', 'Outputs are at most 30 by 30',
              'No hidden answers or parameters in sampled inputs']
PROGRAM = Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH = hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
PATH = Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
NAME = '_canonical_adapter_'+hashlib.sha256(str(PATH).encode()).hexdigest()
if NAME not in sys.modules:
    spec=importlib.util.spec_from_file_location(NAME,PATH)
    module=importlib.util.module_from_spec(spec);sys.modules[NAME]=module;spec.loader.exec_module(module)
adapter=sys.modules[NAME]
PROFILES = {'easy': [(22, 20), (23, 21)], 'medium': [(26, 24), (24, 28)], 'hard': [(30, 30), (29, 29)]}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one input grid, following the ordinary relocated-runner protocol."""
    if overrides:raise TypeError('No override axes are declared')
    adapter.family.integer(seed,0,2**63-1,'seed')
    adapter.family.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is not None and (type(difficulty) is not str or difficulty not in PROFILES):
        raise ValueError('difficulty must be easy, medium, hard or None')
    band='medium' if difficulty is None else difficulty
    randomizer=adapter.family.rng(seed,f'ordinary:{sample_index}:{band}')
    profile=randomizer.choice(PROFILES[band])
    return adapter.family.scene(seed,f'ordinary:{sample_index}:{band}',profile,stress=(band=='hard'))


def rule_mirror(grid):
    return adapter.family.solve(grid,'adaptive')


def self_check(grid):
    try:
        rule_mirror(grid)
        return []
    except (ValueError,TypeError,IndexError) as exc:
        return [str(exc)]
