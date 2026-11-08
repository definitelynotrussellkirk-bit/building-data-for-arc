"""Unapproved public-parent generator. Labels require protected Racket replay."""
from pathlib import Path
import types
RULE_TASK_ID = 'ee_4a21e3da'
TASK_ID = 'public_eval_4a21e3da'
HERE=Path(__file__).resolve().parent
p=HERE/'workspace/parametric/family.py'
G=types.ModuleType('_ordinary_cut_family');G.__file__=str(p)
exec(compile(p.read_bytes(),str(p),'exec'),G.__dict__)
PROGRAM=(HERE/'reference.rkt').read_text()
MIN_TRAIN=2
MAX_TRAIN=6

def generate(seed, sample_index=0, difficulty=None):
    G.integer(seed,0,2**63-1,'seed');G.integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    return G._scene(seed,f'ordinary:{sample_index}',stress=difficulty=='hard' or sample_index%4==3,single=sample_index%3==0)

def rule_mirror(grid):return G.solve(grid,'all')
def self_check(grid):return G.self_check(grid)
