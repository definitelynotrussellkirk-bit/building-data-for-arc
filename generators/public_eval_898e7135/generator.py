"""Public 898e7135: constructive scaled-piece/template assembly inputs."""
RULE_TASK_ID = 'ee_898e7135'
from pathlib import Path
import importlib.util
import hashlib
TASK_ID=GENERATOR_ID='public_eval_898e7135'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
SUMMARY='Match scaled outside pieces to template holes under D4 symmetry, fill, and enlarge the template.'
INVARIANTS=['unique perforated rectangular template','common integer scale','unambiguous shape/color matches','all grids at most 30x30']
AXES={}
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH=hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
spec=importlib.util.spec_from_file_location('public_eval_898e7135_base',Path(__file__).parent/'workspace/parametric/family.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise TypeError('No undeclared override axes')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:raise ValueError('Expected nonnegative integer seed/index')
    return family.scene(seed,f'base:{sample_index}',2+sample_index%2,bent=(sample_index%2==0))
def rule_mirror(grid):return family.solve(grid)
def self_check(grid):
    try:family.analyze(grid);return []
    except (ValueError,IndexError,TypeError) as e:return [str(e)]
