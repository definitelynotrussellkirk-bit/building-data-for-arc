"""Canonical input generator for border-lock key fitting (unapproved authoring)."""
from pathlib import Path
import importlib.util
import sys
RULE_TASK_ID = 'ee_a25697e4'
VERSION = '1.0.0'
_spec=importlib.util.spec_from_file_location('_public_eval_a25697e4_base_model',Path(__file__).resolve().parent/'workspace/parametric/model.py')
_model=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=_model;_spec.loader.exec_module(_model)

def generate(seed=0, sample_index=0, difficulty='medium', **kwargs):
    if kwargs or difficulty not in ('easy','medium','hard') or type(seed) is not int or type(sample_index) is not int or sample_index<0:
        raise ValueError('unsupported generator controls')
    return _model.sample_input(seed,sample_index,query=difficulty=='hard')

def self_check(grid, difficulty=None):
    _model.infer(grid)
    return []
