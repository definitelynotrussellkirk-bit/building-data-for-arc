"""Public 7b5033c1: straighten a path. New unapproved authoring source."""
from pathlib import Path
import types
import hashlib
TASK_ID=GENERATOR_ID='public_eval_7b5033c1'
RULE_TASK_ID = 'ee_7b5033c1'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH=hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY='Traverse the colored path from its reading-order-first endpoint and unroll every cell into a column.'
INVARIANTS=['modal background','single induced four-neighbor path','at most 30 path cells','consecutive runs preserve repeats']
AXES={}
p=Path(__file__).parent/'workspace/parametric/family.py'
G=types.ModuleType('7b5033c1_base_family');G.__file__=str(p)
exec(compile(p.read_bytes(),str(p),'exec'),G.__dict__)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:raise ValueError('nonnegative integer seed and sample_index required')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if overrides:raise TypeError('no override axes')
    return G._scene(seed,f'ordinary:{sample_index}',stress=difficulty=='hard' or sample_index%4==3)
def rule_mirror(g):return G.solve(g,'straighten')
self_check=G.self_check
