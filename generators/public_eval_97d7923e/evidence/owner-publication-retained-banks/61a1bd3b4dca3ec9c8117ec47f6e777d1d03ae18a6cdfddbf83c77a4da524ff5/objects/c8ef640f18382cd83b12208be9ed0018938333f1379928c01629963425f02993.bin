"""Public 97d7923e: rank vertical wires using top-row color-run keys."""
from pathlib import Path
import hashlib
import types

RULE_TASK_ID = 'ee_97d7923e'
TASK_ID = GENERATOR_ID = 'public_eval_97d7923e'
VERSION = '1.0.0'
SUMMARY = 'Use top-row run lengths as ranks among same-color endpoint wires and recolor the selected uniform interiors.'
EXAMPLES_NEEDED = 2
HOME=Path(__file__).resolve().parent
PROGRAM=(HOME/'reference.rkt').read_text()
G=types.ModuleType('_ordinary_rank_relay_'+hashlib.sha256(str(HOME).encode()).hexdigest())
G.__file__=str(HOME/'workspace/parametric/engine.py')
exec(compile(Path(G.__file__).read_bytes(),G.__file__,'exec'),G.__dict__)


def generate(seed=0,sample_index=0,difficulty=None):
    G.integer(seed,0,2**63-1,'seed');G.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    stress=difficulty=='hard' or sample_index%4==3
    return G.make_input(seed,sample_index,'ordinary',30 if stress else None,30 if stress else None,stress=stress)


def rule_mirror(g):return G.solve(g,'rank_only')
def self_check(g):return G.self_check(g)
