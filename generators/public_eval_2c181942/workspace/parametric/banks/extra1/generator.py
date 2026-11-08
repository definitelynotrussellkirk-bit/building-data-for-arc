"""Public 2c181942: rotate loose pieces and dock at colored hub slots."""
from pathlib import Path
import hashlib
import types

RULE_TASK_ID = 'ee_2c181942'
TASK_ID = GENERATOR_ID = 'public_eval_2c181942'
VERSION = '1.0.0'
SUMMARY = 'Identify the colored hub, orient each matching piece by its centered neck, and dock to its keyed side.'
EXAMPLES_NEEDED = 2
HOME=Path(__file__).resolve().parent
PROGRAM=(HOME/'reference.rkt').read_text()
G=types.ModuleType('_ordinary_docking_'+hashlib.sha256(str(HOME).encode()).hexdigest())
G.__file__=str(HOME/'workspace/parametric/engine.py')
exec(compile(Path(G.__file__).read_bytes(),G.__file__,'exec'),G.__dict__)

def generate(seed=0,sample_index=0,difficulty=None):
    G.integer(seed,0,2**63-1,'seed');G.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    return G.make_input(seed,sample_index,'ordinary',stress=difficulty=='hard' or sample_index%4==3)

def rule_mirror(g):return G.solve(g,'matching')
def self_check(g):return G.self_check(g)
