"""Public e8686506: translation-only jigsaw assembly. Not owner-approved."""
from pathlib import Path
import types
import hashlib
TASK_ID=GENERATOR_ID='public_eval_e8686506'
RULE_TASK_ID = 'ee_e8686506'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
PROGRAM=Path(__file__).with_name('reference.rkt').read_text()
RULE_HASH=hashlib.sha256(' '.join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY='Retain the dense scaffold and translate external pieces to tile its rectangle exactly.'
INVARIANTS=['modal background','unique densest area-conserving scaffold','translation-only unique colored exact cover','1..30 grid dimensions']
AXES={}
p=Path(__file__).parent/'workspace/parametric/family.py'
G=types.ModuleType('e8686506_base_family');G.__file__=str(p)
exec(compile(p.read_bytes(),str(p),'exec'),G.__dict__)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:raise ValueError('nonnegative integer seed and sample_index required')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if overrides:raise TypeError('no override axes')
    for attempt in range(128):
        g=G._scene(seed,f'ordinary:{sample_index}',stress=difficulty=='hard' or sample_index%4==3,attempt=attempt)
        if not G.self_check(g):return g
    raise ValueError('bounded scene search exhausted')
def rule_mirror(g):return G.solve(g,'assemble')
self_check=G.self_check
