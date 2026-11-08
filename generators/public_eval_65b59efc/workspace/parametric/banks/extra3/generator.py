"""Fresh color-keyed template-expansion scenes backed by the native adapter."""
from pathlib import Path
import importlib.util
GENERATOR_ID=TASK_ID='public_eval_65b59efc'
RULE_TASK_ID='ee_65b59efc'
VERSION='1.0.0'
SUMMARY='Match permuted coarse masks to colored templates and expand them with aligned swatches.'

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_template_expansion_local_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def generate(seed,sample_index,*,difficulty=None,**overrides):
    a=_adapter();a.integer(seed,0,2**63-1,'seed');a.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unsupported difficulty')
    if overrides:raise ValueError('No generation overrides are declared')
    mixed=(seed+sample_index*104729)%(2**63)
    return a.sample(mixed,'query',3 if difficulty=='hard' else sample_index%4)

def self_check(value,*,difficulty=None,meta=None):return _adapter().input_errors(value)
