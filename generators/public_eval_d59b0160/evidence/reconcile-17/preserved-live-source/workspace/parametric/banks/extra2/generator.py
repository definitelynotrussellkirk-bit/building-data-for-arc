"""Input generator for public parent d59b0160."""
from pathlib import Path
import hashlib,importlib.util,sys
RULE_TASK_ID='ee_d59b0160';TASK_ID='public_eval_d59b0160';VERSION='1.0.0'

def _engine():
    p=Path(__file__).resolve().parent/'workspace/parametric/engine.py';k='_d59_root_'+hashlib.sha256(str(p).encode()).hexdigest()[:16]
    if k not in sys.modules:
        s=importlib.util.spec_from_file_location(k,p);m=importlib.util.module_from_spec(s);sys.modules[k]=m;s.loader.exec_module(m)
    return sys.modules[k]

def generate(seed=0,sample_index=0,difficulty='medium',**overrides):
    e=_engine();e.integer(seed,0,2**63-1,'seed');e.integer(sample_index,0,2**63-1,'sample_index')
    if overrides:raise ValueError('Unknown controls')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    return e.scene(seed,'query' if difficulty=='hard' else 'demo',3 if difficulty=='hard' else sample_index%6)

def self_check(grid,**kwargs):return _engine().self_check(grid)
