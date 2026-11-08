"""Public-parent radial reconstruction generator, not approved until owner review."""
import importlib.util
from pathlib import Path
RULE_TASK_ID = 'ee_db0c5428'
_path=Path(__file__).resolve().parent/"workspace/parametric/family.py"
_spec=importlib.util.spec_from_file_location(__name__+"_family",_path)
_family=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_family)

def generate(seed=0,sample_index=0,difficulty="medium",**kwargs):
    if difficulty not in ("easy","medium","hard"):raise ValueError("Unknown difficulty")
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:raise ValueError("Integer seed/index required")
    return _family.scene(seed,sample_index)

def self_check(grid,**kwargs):
    try:_family.solve(grid)
    except ValueError as exc:return [str(exc)]
    return []
