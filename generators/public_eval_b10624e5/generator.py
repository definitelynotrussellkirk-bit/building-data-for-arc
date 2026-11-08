"""Unapproved public-parent generator; canonical labels come from reference.rkt."""
from pathlib import Path
import importlib.util
import hashlib
RULE_TASK_ID = 'ee_b10624e5'
VERSION = '1.0.0'
_base=Path(__file__).resolve().parent/'workspace/parametric/prototype.py'
_spec=importlib.util.spec_from_file_location('_panel_base_'+hashlib.sha256(str(_base).encode()).hexdigest(),_base)
P=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(P)
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard') or overrides:raise ValueError('unsupported generation control')
    return P.sample(seed,sample_index,stress=(sample_index%4==3))
def self_check(grid,**kwargs):
    try:P.analyse(grid)
    except ValueError as error:return [str(error)]
    return []
