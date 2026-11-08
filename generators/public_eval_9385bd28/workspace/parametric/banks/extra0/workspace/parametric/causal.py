"""Authoring-only ablation: discard input-derived fill values after extraction."""
from pathlib import Path
import importlib.util
import sys
p=Path(__file__).with_name('adapter.py');s=importlib.util.spec_from_file_location('_9385_causal_adapter',p)
a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a)

def descriptions():
    return {'step_a':'Read the isolated legend and recover each keyed rectangle or solid block from the input.',
            'intermediate':'Ordered records of source key, decoded fill color, rectangle bounds and own corner-marker cells.',
            'step_b':'Composite the measured rectangles in episode-selected legend priority, using each decoded fill value.',
            'why_b_depends_on_a':'Geometry and fill colors are input-derived; the compositor cannot choose either from the fixed setting alone. Wrong fill values alter the completed regions.'}

def make_case(episode):
    pair=episode['train'][0];code=episode['program_solution']
    counter=code.replace('(define fill-color (if (= (second entry) 0) bg (second entry)))','(define fill-color bg)')
    if code==counter:raise ValueError('Ablation no longer matches source')
    return {'input':pair['input'],'output':pair['output'],'settings':episode['settings'],'program':code,
            'counterfactual_program':counter,'intermediate_value':a.measure(pair['input']),'ablation':'wrong_intermediate'}
