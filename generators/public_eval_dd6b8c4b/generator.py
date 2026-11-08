"""Fresh maze-collection scenes with source-bound local reference resources."""
from pathlib import Path
import importlib.util
GENERATOR_ID = TASK_ID = 'public_eval_dd6b8c4b'
RULE_TASK_ID = 'ee_dd6b8c4b'
VERSION = '1.0.0'
SUMMARY = 'Use geodesic reachability and rank to move maroon cells into a nine-cell box.'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_collection_local_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def generate(seed,sample_index,*,difficulty=None,**overrides):
    a=_adapter();a.integer(seed,0,2**63-1,'seed');a.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unsupported difficulty')
    if overrides:raise ValueError('No generation overrides are declared')
    mixed=(seed+sample_index*104729)%(2**63)
    return a.sample(mixed,'query',3 if difficulty=='hard' else sample_index%4)


def self_check(value,*,difficulty=None,meta=None):
    return _adapter().input_errors(value)
