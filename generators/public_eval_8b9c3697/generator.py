"""Public 8b9c3697: generate comb sockets and compatible/incompatible red blocks."""
RULE_TASK_ID = 'ee_8b9c3697'
from pathlib import Path
import importlib.util
import hashlib
TASK_ID=GENERATOR_ID='public_eval_8b9c3697'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
SUMMARY='Infer comb middle-tooth lanes, dock nearest compatible red rectangles and blacken their swept trails.'
INVARIANTS=['nonzero nonred modal background','unambiguous three-prong sockets','exact-width aligned solid red rectangles','noninterfering streams','grids at most 30x30']
AXES={}
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH=hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
spec=importlib.util.spec_from_file_location('public_eval_8b9c3697_base',Path(__file__).parent/'workspace/parametric/family.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise TypeError('No undeclared override axes')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:raise ValueError('Expected nonnegative integer seed/index')
    return family.scene(seed,f'base:{sample_index}',2+sample_index%3,sample_index%2)
def rule_mirror(grid):return family.solve(grid)
def self_check(grid):
    try:family.analyze(grid);return []
    except (ValueError,IndexError,TypeError) as e:return [str(e)]
