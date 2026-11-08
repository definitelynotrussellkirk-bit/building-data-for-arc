"""Canonical bf45cf4b input generator; labels are executed by reference.rkt."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_bf45cf4b'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_bf45cf4b_base_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def generate(seed,sample_index=0,difficulty='medium'):
    if type(sample_index) is not int or sample_index<0:
        raise ValueError('sample_index must be a nonnegative integer')
    a=_adapter()
    return a.generate(seed,a.DEFAULT,2,4)['test'][sample_index%4]['input']


def self_check(grid,difficulty='medium'):
    try:
        _adapter().analyze(grid)
        return []
    except ValueError as error:
        return [str(error)]
