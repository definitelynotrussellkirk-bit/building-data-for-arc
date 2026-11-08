"""Canonical public da515329 generator. Native adapter owns the input grammar."""
from pathlib import Path
import importlib.util
import hashlib
RULE_TASK_ID = 'ee_da515329'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_da515329_base_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def generate(seed, sample_index=0, difficulty='medium'):
    if type(sample_index) is not int or sample_index<0:
        raise ValueError('sample_index must be a nonnegative integer')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    # Ordinary sample indices are a draw stream, not a four-query prefix.
    # Domain separation avoids cycling after four samples at one seed.
    draw_seed=int.from_bytes(hashlib.sha256(
        f'base:da515329:{seed}:{sample_index}'.encode()).digest()[:16],'big')
    adapter=_adapter()
    return adapter.generate(draw_seed,adapter.DEFAULT,2,4)['test'][sample_index%4]['input']


def self_check(grid, difficulty='medium'):
    try:
        _adapter().analyze(grid)
        return []
    except ValueError as error:
        return [str(error)]
