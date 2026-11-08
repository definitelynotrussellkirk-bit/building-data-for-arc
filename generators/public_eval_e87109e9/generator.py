"""Ordinary input generator for public parent e87109e9."""
from __future__ import annotations
from pathlib import Path
import importlib.util,sys
RULE_TASK_ID = 'ee_e87109e9'
GENERATOR_VERSION = '1.0.0'
HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_ordinary_e87109e9',HOME/'workspace/parametric/model.py')
model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)

def generate(seed=0,sample_index=0,difficulty='medium'):
    model.integer(seed,0,2**63-1,'seed');model.integer(sample_index,0,2**31-1,'sample_index')
    if difficulty is None: difficulty='medium'
    if difficulty not in ('easy','medium','hard'): raise ValueError('difficulty must be easy, medium, or hard')
    return model.sample_input(seed,sample_index,'base',difficulty)

def self_check(grid,difficulty='medium'):
    try: model.analyze(grid)
    except (TypeError,ValueError,IndexError) as exc: return [str(exc)]
    return []
