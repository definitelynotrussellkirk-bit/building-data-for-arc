"""Ordinary canonical input generator; unapproved public-evaluation authoring."""
from pathlib import Path
import importlib.util
import sys
RULE_TASK_ID = 'ee_6ffbe589'
GENERATOR_VERSION = '1.0.0'
_path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
_spec=importlib.util.spec_from_file_location('_public_6ff_generator_adapter',_path)
_adapter=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=_adapter;_spec.loader.exec_module(_adapter)

def generate(seed=0, sample_index=0, difficulty='medium', **kwargs):
    if kwargs:raise ValueError('No extra generator controls are declared')
    if difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    if type(sample_index) is not int or not 0<=sample_index<2**63:raise ValueError('Invalid sample_index')
    split='test' if difficulty=='hard' else 'train'
    return _adapter.sample(seed,sample_index,split)

def self_check(grid,difficulty='medium'):
    try:_adapter.measure(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
