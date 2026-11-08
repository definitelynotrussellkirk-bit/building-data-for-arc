"""Canonical public abc82100 generator. Native adapter owns the input grammar."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_abc82100'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_abc82100_base_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def generate(seed, sample_index=0, difficulty='medium'):
    if type(sample_index) is not int or sample_index<0:
        raise ValueError('sample_index must be a nonnegative integer')
    adapter=_adapter()
    return adapter.generate(seed,adapter.DEFAULT,2,4)['test'][sample_index%4]['input']


def self_check(grid, difficulty='medium'):
    try:
        _adapter().analyze(grid)
        return []
    except ValueError as error:
        return [str(error)]
