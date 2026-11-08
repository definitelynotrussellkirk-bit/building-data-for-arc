"""Ordinary canonical input generator; unapproved public-evaluation authoring."""
from pathlib import Path
import importlib.util
import sys
RULE_TASK_ID = 'ee_9385bd28'
GENERATOR_VERSION = '1.0.0'
p=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
s=importlib.util.spec_from_file_location('_public_9385_generator_adapter',p)
a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a)

def generate(seed=0,sample_index=0,difficulty='medium',**kwargs):
    if kwargs:raise ValueError('No extra generator controls are declared')
    if difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    if type(sample_index) is not int or not 0<=sample_index<2**63:raise ValueError('Invalid sample_index')
    return a.sample(seed,sample_index,'test' if difficulty=='hard' else 'train')

def self_check(grid,difficulty='medium'):
    try:a.measure(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
