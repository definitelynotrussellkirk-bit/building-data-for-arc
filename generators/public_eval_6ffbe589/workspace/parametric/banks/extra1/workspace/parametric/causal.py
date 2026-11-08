"""Authoring-only causal ablation recipe: replace measured tally vector by zeros."""
from pathlib import Path
import importlib.util
import sys
p=Path(__file__).with_name('adapter.py');s=importlib.util.spec_from_file_location('_6ff_causal_adapter',p)
a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a)

def descriptions():
    return {'step_a':'Recover the concentric square and count external instruction cells separately for each picture color.',
            'intermediate':'The input-derived crop bounds and vector mapping each color to its tally count.',
            'step_b':'Rotate each recovered color mask by the directed tally count modulo four and compose the masks.',
            'why_b_depends_on_a':'The amount differs per color and input. Without the measured counts, the later rotations cannot be chosen.'}

def make_case(episode):
    pair=episode['train'][0];code=episode['program_solution']
    counter=code.replace('(define turns (modulo (* turn-sign (second entry)) 4))','(define turns 0)')
    if counter==code:raise ValueError('Ablation no longer matches source')
    return {'input':pair['input'],'output':pair['output'],'settings':episode['settings'],'program':code,
            'counterfactual_program':counter,'intermediate_value':a.measure(pair['input']),'ablation':'wrong_intermediate'}
