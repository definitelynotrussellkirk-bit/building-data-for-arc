"""Unapproved public-evaluation family; labels are replayed during preflight."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_6e453dd6'

def generate(seed=0, train=3, test=4):
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_6e453dd6_native',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.generate(seed,{'signal_policy':'all_exposed'},train,test)
