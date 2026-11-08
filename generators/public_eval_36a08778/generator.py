"""Fresh falling-ray scenes with local parametric resources."""
from pathlib import Path
import importlib.util

GENERATOR_ID=TASK_ID='public_eval_36a08778'
RULE_TASK_ID='ee_36a08778'
VERSION='1.0.0'
SUMMARY='Propagate top-edge rays downward and route them around horizontal red obstacles.'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_falling_ray_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def generate(seed,sample_index,*,difficulty=None,**overrides):
    a=_adapter();a.integer(seed,0,2**63-1,'seed');a.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unsupported difficulty')
    if overrides:raise ValueError('No generation overrides are declared')
    mixed=(seed+sample_index*104729)%(2**63)
    return a.sample(mixed,'query',3 if difficulty=='hard' else sample_index%4)


def self_check(value,*,difficulty=None,meta=None):return _adapter().input_errors(value)
