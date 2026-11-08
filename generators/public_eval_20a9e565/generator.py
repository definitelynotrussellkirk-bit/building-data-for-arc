"""Unapproved public-parent sequence generator; reference.rkt owns canonical labels."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_20a9e565'
VERSION='1.0.0'
TASK_ID='public_eval_20a9e565'
GENERATOR_ID=TASK_ID
SUMMARY='Extrapolate the growing object sequence and return the gray-corner crop.'
AXES={}
INVARIANTS=['Two gray crop corners','At least three ordered growth examples','Learned texture or validated rail/arch grammar','Unique selected future object']

def _family():
    path=Path(__file__).resolve().parent/'workspace/parametric/family.py'
    s=importlib.util.spec_from_file_location('_20a9e565_generator_family',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if overrides or difficulty not in (None,'easy','medium','hard'):raise ValueError('Undeclared control')
    return _family().scene(seed,sample_index)

def self_check(g):
    try:
        m=_family();m.grid(g);m.grid(m.solve(g));return []
    except (TypeError,ValueError,IndexError)as e:return [str(e)]
