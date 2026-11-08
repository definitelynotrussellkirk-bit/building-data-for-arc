"""Unapproved public-parent jigsaw generator; canonical labels execute reference.rkt."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_f560132c'
VERSION='1.0.0'
TASK_ID='public_eval_f560132c'
GENERATOR_ID=TASK_ID
SUMMARY='Assemble rotated scattered pieces into a square and recolor them using the embedded spatial key.'
AXES={}
INVARIANTS=['One key-bearing piece','Four or nine pieces','Unique square assembly under rotations','Distinct spatial key colors']

def _family():
    path=Path(__file__).resolve().parent/'workspace/parametric/family.py'
    spec=importlib.util.spec_from_file_location('_f560132c_generator_family',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if overrides or difficulty not in (None,'easy','medium','hard'):raise ValueError('Undeclared control')
    return _family().scene(seed,sample_index)

def self_check(g):
    try:
        m=_family();m.grid(g)
        if len(m.arrangements(g,2))!=1:return ['Ambiguous or impossible jigsaw']
        return []
    except (TypeError,ValueError,IndexError)as e:return [str(e)]
